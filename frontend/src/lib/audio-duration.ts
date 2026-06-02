// Robust audio duration extraction with multiple fallback strategies.
//
// Browser-recorded WebM (Chrome/Edge/Firefox via MediaRecorder) often lacks
// duration metadata in the container header, causing HTMLAudioElement to report
// Infinity or NaN. The Web Audio API decodes the full stream and always returns
// the correct duration regardless of metadata.

export async function getAudioDuration(blob: Blob): Promise<number> {
  console.debug(
    "[audio-duration] starting  type=%s  size=%d bytes",
    blob.type,
    blob.size,
  )

  // Strategy A: HTMLAudioElement — fast, works for MP3/WAV/MP4/FLAC and most WebM
  try {
    const d = await _durationFromElement(blob)
    console.debug("[audio-duration] Strategy A (HTMLAudioElement): %.3f s", d)
    return d
  } catch (e) {
    console.debug("[audio-duration] Strategy A failed:", e)
  }

  // Strategy B: Web Audio API — decodes the full audio stream; always succeeds
  // even when the container header lacks a duration element (e.g. Chrome WebM)
  try {
    const d = await _durationFromWebAudioApi(blob)
    console.debug("[audio-duration] Strategy B (Web Audio API): %.3f s", d)
    return d
  } catch (e) {
    console.debug("[audio-duration] Strategy B failed:", e)
  }

  console.error(
    "[audio-duration] all strategies failed  type=%s  size=%d",
    blob.type,
    blob.size,
  )
  throw new Error("Could not determine audio duration")
}

function _durationFromElement(blob: Blob): Promise<number> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob)
    const audio = new Audio()
    audio.preload = "metadata"

    const cleanup = () => URL.revokeObjectURL(url)

    audio.onloadedmetadata = () => {
      cleanup()
      const { duration } = audio
      if (isFinite(duration) && duration > 0) {
        resolve(duration)
      } else {
        reject(
          new Error(`HTMLAudioElement: invalid duration (${duration})`),
        )
      }
    }

    audio.onerror = () => {
      cleanup()
      reject(new Error("HTMLAudioElement: failed to load audio"))
    }

    audio.src = url
  })
}

async function _durationFromWebAudioApi(blob: Blob): Promise<number> {
  const arrayBuffer = await blob.arrayBuffer()
  const ctx = new AudioContext()
  try {
    const buf = await ctx.decodeAudioData(arrayBuffer)
    const { duration } = buf
    if (!isFinite(duration) || duration <= 0) {
      throw new Error(`Web Audio API: invalid duration (${duration})`)
    }
    return duration
  } finally {
    await ctx.close().catch(() => {})
  }
}
