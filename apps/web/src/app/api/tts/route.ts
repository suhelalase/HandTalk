import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { text } = await req.json();
    if (!text || typeof text !== 'string') {
      return NextResponse.json({ error: 'Invalid text' }, { status: 400 });
    }

    const headerKey = req.headers.get('x-murf-api-key');
    const apiKey = headerKey || process.env.MURF_API_KEY;
    let apiBaseUrl = process.env.MURF_API_URL || 'https://api.murf.ai/v1/speech';
    // Murf currently serves /v1/speech/generate on api.murf.ai (not global.api.murf.ai)
    apiBaseUrl = apiBaseUrl.replace('https://global.api.murf.ai', 'https://api.murf.ai');
    apiBaseUrl = apiBaseUrl.replace('http://global.api.murf.ai', 'http://api.murf.ai');

    if (!apiKey) {
      return NextResponse.json({ error: 'Murf API key missing' }, { status: 400 });
    }

    // Murf Falcon TTS request (adjust payload based on Murf docs)
    const generateUrl = apiBaseUrl.endsWith('/generate') ? apiBaseUrl : `${apiBaseUrl}/generate`;
    const murfPayload = {
      text,
      voice_id: 'Terrell',
      voiceId: 'Terrell',
      locale: 'en-US',
      format: 'MP3',
      modelVersion: 'GEN2',
    };

    const murfRes = await fetch(generateUrl, {
      method: 'POST',
      headers: {
        'api-key': apiKey,
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(murfPayload),
    });

    if (!murfRes.ok) {
      const errText = await murfRes.text();
      console.error('Murf API error:', murfRes.status, errText);
      return NextResponse.json(
        {
          error: 'TTS request failed',
          murfStatus: murfRes.status,
          murfBody: errText,
          murfUrl: generateUrl,
        },
        { status: murfRes.status }
      );
    }

    const murfJson = (await murfRes.json()) as {
      audioFile?: string;
      audio_file?: string;
      encodedAudio?: string;
      encoded_audio?: string;
    };

    const audioFileUrl = murfJson.audioFile || murfJson.audio_file;
    const encodedAudio = murfJson.encodedAudio || murfJson.encoded_audio;

    let audioBuffer: ArrayBuffer;
    if (encodedAudio) {
      const base64 = encodedAudio.includes(',') ? encodedAudio.split(',', 2)[1] : encodedAudio;
      audioBuffer = Buffer.from(base64, 'base64');
    } else if (audioFileUrl) {
      const audioRes = await fetch(audioFileUrl);
      if (!audioRes.ok) {
        const errText = await audioRes.text();
        console.error('Murf audio fetch error:', audioRes.status, errText);
        return NextResponse.json({ error: 'Failed to fetch audio file' }, { status: 500 });
      }
      audioBuffer = await audioRes.arrayBuffer();
    } else {
      console.error('Murf API response missing audioFile/encodedAudio', murfJson);
      return NextResponse.json({ error: 'Invalid TTS response' }, { status: 500 });
    }

    return new NextResponse(audioBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'no-cache',
      },
    });
  } catch (err) {
    console.error('TTS error:', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
