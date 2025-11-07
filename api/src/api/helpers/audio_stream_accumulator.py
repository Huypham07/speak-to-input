from __future__ import annotations

import asyncio
import io
import logging
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from application.services import VoiceService
from pydub import AudioSegment
from rapidfuzz import fuzz
from shared.settings import Settings

logger = logging.getLogger(__name__)


class AudioStreamAccumulator:
    """
    AudioStreamAccumulator - concurrent-safe streaming transcription accumulator.

    Key features:
    - Safe copy/reset of buffer under an asyncio.Lock to avoid races with add_chunk.
    - Offloads heavy voice_service calls into asyncio.Tasks; tracks pending tasks.
    - Limits concurrency via Semaphore (max_concurrent_tasks).
    - Stores results in seg_results dict keyed by sequential seg_id (safe ordering).
    - get_transcription() waits for all pending tasks (including final flush) then merges.
    - Optional on_segment callback called whenever a segment completes:
        on_segment(seg_id: int, text: str) -> None | awaitable.
    """

    def __init__(
        self,
        settings: Settings,
        voice_service: Optional[VoiceService] = None,
        target_seconds: float = 10.0,
        overlap_seconds: float = 2.0,
        max_overlap: int = 10,
        min_overlap: int = 3,
        max_concurrent_tasks: int = 3,
    ):
        self.settings = settings
        self.voice_service: VoiceService = voice_service or VoiceService(settings)
        self.target_seconds = target_seconds
        self.overlap_seconds = overlap_seconds
        self.max_overlap = max_overlap
        self.min_overlap = min_overlap

        self._lock = asyncio.Lock()  # protect buffer and id assignment & seg_results
        self._sem = asyncio.Semaphore(max_concurrent_tasks)

        # runtime state
        self.reset_state()

        # optional callback: called when a segment finishes
        # signature: (seg_id: int, text: str) -> None or coroutine
        self.on_segment: Optional[Callable[[int, str], None]] = None

    def reset_state(self):
        """Reset transient state but keep config and primitives."""
        self.buffer = AudioSegment.empty()
        self.total_duration = 0.0

        # results: seg_id -> text (may fill out of order)
        self.seg_results: Dict[int, str] = {}
        self._next_seg_id = 0  # assigned sequentially when a segment is created

        # list of pending asyncio.Tasks handling segments
        self.pending_tasks: List[asyncio.Task] = []

        self.closed = False

    def start_new_session(self):
        """Explicitly start a new session (reset transient state)."""
        self.reset_state()
        logger.info('AudioStreamAccumulator: started new session')

    async def add_chunk(self, chunk_bytes: bytes):
        """
        Add incoming WAV chunk bytes. When buffer length >= target_seconds,
        create a processing task for the current segment (copy buffer -> bytes).
        """
        try:
            audio = AudioSegment.from_file(io.BytesIO(chunk_bytes), format='wav')
        except Exception as e:
            logger.error(f'Failed to read audio chunk: {e}')
            return

        async with self._lock:
            # append to buffer safely
            self.buffer += audio
            self.total_duration = self.buffer.duration_seconds

            if self.total_duration >= self.target_seconds:
                # copy current segment (slice returns new AudioSegment)
                segment = self.buffer[:]
                # compute overlap tail from the copied segment
                overlap = (
                    segment[-int(self.overlap_seconds * 1000):]
                    if self.overlap_seconds > 0
                    else AudioSegment.empty()
                )
                # reset buffer to the overlap so producer can continue
                self.buffer = overlap
                self.total_duration = self.buffer.duration_seconds

                # export WAV bytes outside the lock to avoid heavy ops in lock
                out = io.BytesIO()
                segment.export(out, format='wav')
                wav_bytes = out.getvalue()

                # assign seg_id under lock (we are still under lock here)
                seg_id = self._next_seg_id
                self._next_seg_id += 1

                # create processing task and track it
                task = asyncio.create_task(self._process_segment_from_bytes(seg_id, wav_bytes))
                self.pending_tasks.append(task)

    async def _process_segment_from_bytes(self, seg_id: int, wav_bytes: bytes):
        """
        Process already-exported WAV bytes for a given seg_id.
        This runs as a background task. It will:
        - await the voice_service under a Semaphore (limit concurrency)
        - write result into seg_results under lock
        - call on_segment callback if set
        - remove itself from pending_tasks
        """
        try:
            async with self._sem:
                # call voice service (may raise)
                if wav_bytes:
                    text = await self.voice_service.speech_to_text(audio_bytes=wav_bytes)
                else:
                    logger.error('Cảnh báo: Không thể xử lý chunk vì đối tượng là None.')
                    text = ''

            # store result under lock to prevent races with other writes
            async with self._lock:
                self.seg_results[seg_id] = text

            # optional callback (allow coroutine)
            if self.on_segment:
                try:
                    res = self.on_segment(seg_id, text)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as cb_exc:
                    logger.exception('on_segment callback raised an exception', exc_info=cb_exc)

        except Exception as e:
            # store empty or error marker to keep ordering info if desired
            logger.exception(f'Exception while processing segment {seg_id} by error {e}')
            async with self._lock:
                # store None or empty string so merging can skip or note errors
                self.seg_results[seg_id] = ''

        finally:
            # cleanup: remove current task from pending_tasks if present
            current = asyncio.current_task()
            if current is not None:
                try:
                    # list remove under lock to be safe
                    async with self._lock:
                        if current in self.pending_tasks:
                            self.pending_tasks.remove(current)
                except Exception:
                    # ignore cleanup errors
                    logger.debug('Failed to remove task from pending_tasks', exc_info=True)

    async def get_transcription(self, auto_reset: bool = True) -> str:
        """
        Wait for all pending segment tasks to finish (flush final buffer first),
        then merge results in seg_id order and return the final transcription.
        """
        # if there's remaining audio in buffer -> create final segment task
        async with self._lock:
            has_buffer = len(self.buffer) > 0 and not self.closed
            if has_buffer:
                # copy current buffer -> segment and reset buffer to empty
                segment = self.buffer[:]
                overlap = AudioSegment.empty()  # final: don't keep overlap
                self.buffer = overlap
                self.total_duration = 0.0

                out = io.BytesIO()
                segment.export(out, format='wav')
                wav_bytes = out.getvalue()

                seg_id = self._next_seg_id
                self._next_seg_id += 1
                task = asyncio.create_task(self._process_segment_from_bytes(seg_id, wav_bytes))
                self.pending_tasks.append(task)

        # Await all pending tasks (if any)
        # Copy the list to avoid race on concurrent appends/removals; but we wait on current snapshot.
        # We also allow tasks created after this point? The design here ensures producer shouldn't create new tasks
        # after final flush if client intends to finish. If producers still add, they will be new tasks not awaited here.
        while True:
            async with self._lock:
                tasks_snapshot = list(self.pending_tasks)
            if not tasks_snapshot:
                break
            # wait for current batch to finish; any new tasks appended while awaiting will be awaited in next loop iteration
            await asyncio.gather(*tasks_snapshot, return_exceptions=True)

        # Now all segment tasks finished -> merge in order
        merged = ''
        # iterate seg_ids from 0 .. max-1
        if self.seg_results:
            max_id = max(self.seg_results.keys())
            for i in range(max_id + 1):
                seg_text = self.seg_results.get(i)
                if seg_text is None or seg_text == '':
                    # skip empty segments (or you may want to insert a placeholder)
                    continue
                merged = self.merge_text(merged, seg_text)

        self.closed = True

        final_text = merged.strip()
        if auto_reset:
            self.reset_state()

        return final_text

    def merge_text(self, old_text: str, new_seg: str) -> str:
        """
        Merge new_seg into old_text using fuzzy overlap detection.
        """
        if not old_text:
            return new_seg.strip()

        t1, t2 = old_text, new_seg
        best_score = 0
        best_i = 0

        # limit overlap window
        max_i = min(len(t1), self.max_overlap)
        for i in range(self.min_overlap, max_i):
            suffix = t1[-i:]
            prefix = t2[:i]
            score = fuzz.ratio(suffix, prefix)
            if score > best_score:
                best_score = score
                best_i = i

        if best_score > 70 and best_i > 0:
            merged = t1 + t2[best_i:]
        else:
            merged = t1 + ' ' + t2

        return merged.strip()
