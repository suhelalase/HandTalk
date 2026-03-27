import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { text } = await req.json();
    if (!text || typeof text !== 'string') {
      return NextResponse.json({ error: 'Invalid text' }, { status: 400 });
    }

    const headerKey = req.headers.get('x-gemini-api-key');
    const apiKey = headerKey || process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Gemini API key missing' }, { status: 400 });
    }

    const base = 'https://generativelanguage.googleapis.com/v1beta';
    const key = encodeURIComponent(apiKey);

    const pickModel = async (): Promise<string> => {
      const preferred = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro'];
      try {
        const listUrl = `${base}/models?key=${key}`;
        const listRes = await fetch(listUrl);
        if (!listRes.ok) return preferred[0];
        const listJson = (await listRes.json()) as any;
        const models: any[] = Array.isArray(listJson?.models) ? listJson.models : [];
        for (const id of preferred) {
          const found = models.find((m) => typeof m?.name === 'string' && m.name.endsWith(`/models/${id}`));
          if (found && Array.isArray(found?.supportedGenerationMethods)) {
            if (found.supportedGenerationMethods.includes('generateContent')) return id;
          }
        }
        // fallback: first model that supports generateContent
        const anyModel = models.find(
          (m) => Array.isArray(m?.supportedGenerationMethods) && m.supportedGenerationMethods.includes('generateContent')
        );
        if (anyModel?.name && typeof anyModel.name === 'string') {
          return anyModel.name.split('/').pop() || preferred[0];
        }
        return preferred[0];
      } catch {
        return preferred[0];
      }
    };

    const modelId = await pickModel();
    const url = `${base}/models/${encodeURIComponent(modelId)}:generateContent?key=${key}`;

    const prompt =
      'You are a real-time speech/text post-processor. Convert the given noisy letter-by-letter transcript into correct English words.\n' +
      'Rules:\n' +
      '- Return ONLY the corrected text (no quotes, no markdown).\n' +
      '- Keep it short.\n' +
      '- If it is already correct, return it unchanged.\n' +
      '- Do not add extra words that are not implied.\n' +
      `Input: ${text}`;

    const geminiRes = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.2, maxOutputTokens: 64 },
      }),
    });

    if (!geminiRes.ok) {
      const errText = await geminiRes.text();
      let retryAfterSeconds: number | undefined;
      try {
        const parsed = JSON.parse(errText);
        const details = parsed?.error?.details;
        if (Array.isArray(details)) {
          const retryInfo = details.find((d: any) => d?.['@type'] === 'type.googleapis.com/google.rpc.RetryInfo');
          const delay: string | undefined = retryInfo?.retryDelay;
          if (typeof delay === 'string') {
            const m = delay.match(/(\d+)/);
            if (m) retryAfterSeconds = Number(m[1]);
          }
        }
      } catch {
        // ignore
      }

      const headerRetryAfter = geminiRes.headers.get('retry-after');
      if (!retryAfterSeconds && headerRetryAfter) {
        const n = Number(headerRetryAfter);
        if (!Number.isNaN(n)) retryAfterSeconds = n;
      }

      const res = NextResponse.json(
        {
          error: 'Gemini request failed',
          geminiStatus: geminiRes.status,
          geminiBody: errText,
          retryAfterSeconds,
        },
        { status: geminiRes.status }
      );
      if (retryAfterSeconds && Number.isFinite(retryAfterSeconds)) {
        res.headers.set('Retry-After', String(Math.max(1, Math.floor(retryAfterSeconds))));
      }
      return res;
    }

    const geminiJson = (await geminiRes.json()) as any;
    const correctedText: string | undefined = geminiJson?.candidates?.[0]?.content?.parts?.[0]?.text;

    // Gemini can return no candidates/content (e.g. safety block, empty output). In that case,
    // fall back to the original text so the pipeline can continue.
    if (!correctedText || typeof correctedText !== 'string') {
      const finishReason = geminiJson?.candidates?.[0]?.finishReason;
      return NextResponse.json({ correctedText: text.trim(), geminiEmpty: true, finishReason });
    }

    return NextResponse.json({ correctedText: correctedText.trim() });
  } catch (err) {
    console.error('Gemini error:', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
