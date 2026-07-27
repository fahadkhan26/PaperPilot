const API_BASE_URL = 'http://172.20.214.117:8000';

// Sentinel the backend writes into the stream if the chain throws mid-response.
// Anything after it in the stream is treated as an error message, not chat text.
const ERROR_MARKER = '\u0000ERR\u0000';

/**
 * Uploads a PDF to the backend ingestion pipeline.
 */
export async function uploadPdf(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Upload failed.');
  }
  return data;
}

/**
 * Streams a chat response chunk-by-chunk as it is generated, instead of
 * waiting for the full response — mirrors `for chunk in chain.stream(...)`.
 *
 * @param {string} query
 * @param {(chunk: string) => void} onChunk called for every piece of text as it arrives
 * @param {() => void} onDone called once the stream finishes successfully
 * @param {(message: string) => void} onError called on any failure (network, HTTP, or mid-stream)
 */
export async function streamChat(query, onChunk, onDone, onError) {
  try {
    const res = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    if (!res.ok || !res.body) {
      let detail = 'Something went wrong while reaching the server.';
      try {
        const data = await res.json();
        detail = data.detail || detail;
      } catch (_) {
        /* response wasn't JSON, keep default message */
      }
      onError(detail);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunkText = decoder.decode(value, { stream: true });

      if (chunkText.includes(ERROR_MARKER)) {
        const [before, after] = chunkText.split(ERROR_MARKER);
        if (before) onChunk(before);
        onError(after || 'Something went wrong while generating the response.');
        return;
      }

      onChunk(chunkText);
    }

    onDone();
  } catch (err) {
    onError(err.message || 'Network error. Please check your connection.');
  }
}
