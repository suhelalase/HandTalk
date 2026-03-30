declare module '@mediapipe/hands' {
  export class Hands {
    constructor(options?: any);
    setOptions(options: any): void;
    onResults(cb: (results: any) => void): void;
    send(input: any): Promise<void>;
    close(): void;
  }
}

declare module '@mediapipe/camera_utils' {
  export class Camera {
    constructor(video: HTMLVideoElement, options: any);
    start(): void;
    stop(): void;
  }
}
