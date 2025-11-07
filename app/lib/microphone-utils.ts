/**
 * Utility functions for managing microphone cleanup
 */

/**
 * Stop all tracks in a MediaStream and log the cleanup
 */
export function stopMediaStream(stream: MediaStream | null, context: string = "unknown"): void {
  if (!stream) {
    return;
  }

  const tracks = stream.getTracks();

  if (tracks.length === 0) {
    return;
  }

  tracks.forEach((track) => {
    const label = track.label || "unlabeled";
    const kind = track.kind;
    const stateBefore = track.readyState;

    track.stop();

    const stateAfter = track.readyState;
  });
}

/**
 * Stop MediaRecorder safely
 */
export function stopMediaRecorder(recorder: MediaRecorder | null, context: string = "unknown"): void {
  if (!recorder) {
    return;
  }

  const stateBefore = recorder.state;

  if (stateBefore === "inactive") {
    return;
  }

  try {
    recorder.stop();
  } catch (err) {
    console.error(`🎬 [${context}] Error stopping recorder:`, err);
  }
}

/**
 * Complete cleanup of all microphone resources
 */
export function cleanupMicrophoneResources(
  stream: MediaStream | null,
  recorder: MediaRecorder | null,
  context: string = "cleanup"
): void {
  stopMediaRecorder(recorder, context);
  stopMediaStream(stream, context);
}
