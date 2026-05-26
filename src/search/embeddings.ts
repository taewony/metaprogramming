import type { EmbeddingProvider } from './provider.js';

const MAX_BATCH = 2048;

export async function embed(
  texts: string[],
  provider: EmbeddingProvider,
  key: string,
): Promise<number[][]> {
  const results: number[][] = [];

  // Remove gemini- prefix if present for the actual API call
  const actualKey = key.startsWith('gemini-') ? key.slice(7) : key;

  for (let i = 0; i < texts.length; i += MAX_BATCH) {
    const batch = texts.slice(i, i + MAX_BATCH);

    if (provider.name === 'gemini') {
      const resp = await fetch(
        `${provider.apiBase}/${provider.model}:batchEmbedContents?key=${actualKey}`,
        {
          method: 'POST',
          headers: provider.headers(key),
          body: JSON.stringify({
            requests: batch.map((t) => ({
              model: provider.model,
              content: { parts: [{ text: t }] },
            })),
          }),
        },
      );

      if (!resp.ok) {
        const body = await resp.text();
        throw new Error(
          `Embedding API error (${resp.status}): ${body.slice(0, 200)}`,
        );
      }

      const json = (await resp.json()) as {
        embeddings: { values: number[] }[];
      };
      for (const item of json.embeddings) {
        results.push(item.values);
      }
    } else {
      const resp = await fetch(`${provider.apiBase}/embeddings`, {
        method: 'POST',
        headers: provider.headers(key),
        body: JSON.stringify({
          model: provider.model,
          input: batch,
        }),
      });

      if (!resp.ok) {
        const body = await resp.text();
        throw new Error(
          `Embedding API error (${resp.status}): ${body.slice(0, 200)}`,
        );
      }

      const json = (await resp.json()) as {
        data: { embedding: number[]; index: number }[];
      };
      const sorted = json.data.sort((a, b) => a.index - b.index);
      for (const item of sorted) {
        results.push(item.embedding);
      }
    }
  }

  return results;
}
