class RecorderProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input && input[0]) {
      // log temporal de diagnóstico
      if (!this._logged) {
        this.port.postMessage({ debug: true, canales: input.length, tam: input[0].length });
        this._logged = true;
      }
      this.port.postMessage(input[0].slice(0));
    }
    return true;
  }
}
registerProcessor('recorder-processor', RecorderProcessor);