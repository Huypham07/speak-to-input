/**
 * AudioWorklet processor for capturing raw PCM audio data
 * This runs on a separate audio thread for better performance
 */

class RecorderWorkletProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.bufferSize = 4096; // Accumulate chunks
    this.buffer = [];
    this.bufferLength = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];

    // If no input, return true to keep processor alive
    if (!input || !input[0]) {
      return true;
    }

    // Get first channel (mono)
    const inputData = input[0];

    // Copy data to avoid issues with buffer reuse
    const chunk = new Float32Array(inputData.length);
    chunk.set(inputData);

    this.buffer.push(chunk);
    this.bufferLength += chunk.length;

    // Send chunks when buffer reaches threshold
    if (this.bufferLength >= this.bufferSize) {
      // Merge all chunks
      const merged = new Float32Array(this.bufferLength);
      let offset = 0;
      for (const buf of this.buffer) {
        merged.set(buf, offset);
        offset += buf.length;
      }

      // Send to main thread
      this.port.postMessage({
        type: 'audio-data',
        data: merged,
      });

      // Reset buffer
      this.buffer = [];
      this.bufferLength = 0;
    }

    // Keep processor alive
    return true;
  }
}

registerProcessor('recorder-worklet', RecorderWorkletProcessor);
