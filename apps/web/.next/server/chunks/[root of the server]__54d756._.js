module.exports = {

"[externals]/ [external] (next/dist/compiled/next-server/app-route.runtime.dev.js, cjs)": (function(__turbopack_context__) {

var { r: __turbopack_require__, f: __turbopack_module_context__, i: __turbopack_import__, s: __turbopack_esm__, v: __turbopack_export_value__, n: __turbopack_export_namespace__, c: __turbopack_cache__, M: __turbopack_modules__, l: __turbopack_load__, j: __turbopack_dynamic__, P: __turbopack_resolve_absolute_path__, U: __turbopack_relative_url__, R: __turbopack_resolve_module_id_path__, b: __turbopack_worker_blob_url__, g: global, __dirname, x: __turbopack_external_require__, y: __turbopack_external_import__, m: module, e: exports, t: require } = __turbopack_context__;
{
const mod = __turbopack_external_require__("next/dist/compiled/next-server/app-route.runtime.dev.js");

module.exports = mod;
}}),
"[externals]/ [external] (@opentelemetry/api, cjs)": (function(__turbopack_context__) {

var { r: __turbopack_require__, f: __turbopack_module_context__, i: __turbopack_import__, s: __turbopack_esm__, v: __turbopack_export_value__, n: __turbopack_export_namespace__, c: __turbopack_cache__, M: __turbopack_modules__, l: __turbopack_load__, j: __turbopack_dynamic__, P: __turbopack_resolve_absolute_path__, U: __turbopack_relative_url__, R: __turbopack_resolve_module_id_path__, b: __turbopack_worker_blob_url__, g: global, __dirname, x: __turbopack_external_require__, y: __turbopack_external_import__, m: module, e: exports, t: require } = __turbopack_context__;
{
const mod = __turbopack_external_require__("@opentelemetry/api");

module.exports = mod;
}}),
"[externals]/ [external] (next/dist/compiled/next-server/app-page.runtime.dev.js, cjs)": (function(__turbopack_context__) {

var { r: __turbopack_require__, f: __turbopack_module_context__, i: __turbopack_import__, s: __turbopack_esm__, v: __turbopack_export_value__, n: __turbopack_export_namespace__, c: __turbopack_cache__, M: __turbopack_modules__, l: __turbopack_load__, j: __turbopack_dynamic__, P: __turbopack_resolve_absolute_path__, U: __turbopack_relative_url__, R: __turbopack_resolve_module_id_path__, b: __turbopack_worker_blob_url__, g: global, __dirname, x: __turbopack_external_require__, y: __turbopack_external_import__, m: module, e: exports, t: require } = __turbopack_context__;
{
const mod = __turbopack_external_require__("next/dist/compiled/next-server/app-page.runtime.dev.js");

module.exports = mod;
}}),
"[externals]/ [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)": (function(__turbopack_context__) {

var { r: __turbopack_require__, f: __turbopack_module_context__, i: __turbopack_import__, s: __turbopack_esm__, v: __turbopack_export_value__, n: __turbopack_export_namespace__, c: __turbopack_cache__, M: __turbopack_modules__, l: __turbopack_load__, j: __turbopack_dynamic__, P: __turbopack_resolve_absolute_path__, U: __turbopack_relative_url__, R: __turbopack_resolve_module_id_path__, b: __turbopack_worker_blob_url__, g: global, __dirname, x: __turbopack_external_require__, y: __turbopack_external_import__, m: module, e: exports, t: require } = __turbopack_context__;
{
const mod = __turbopack_external_require__("next/dist/server/app-render/work-unit-async-storage.external.js");

module.exports = mod;
}}),
"[externals]/ [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)": (function(__turbopack_context__) {

var { r: __turbopack_require__, f: __turbopack_module_context__, i: __turbopack_import__, s: __turbopack_esm__, v: __turbopack_export_value__, n: __turbopack_export_namespace__, c: __turbopack_cache__, M: __turbopack_modules__, l: __turbopack_load__, j: __turbopack_dynamic__, P: __turbopack_resolve_absolute_path__, U: __turbopack_relative_url__, R: __turbopack_resolve_module_id_path__, b: __turbopack_worker_blob_url__, g: global, __dirname, x: __turbopack_external_require__, y: __turbopack_external_import__, m: module, e: exports, t: require } = __turbopack_context__;
{
const mod = __turbopack_external_require__("next/dist/server/app-render/work-async-storage.external.js");

module.exports = mod;
}}),
"[project]/apps/web/src/app/api/gemini/route.ts [app-route] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { r: __turbopack_require__, f: __turbopack_module_context__, i: __turbopack_import__, s: __turbopack_esm__, v: __turbopack_export_value__, n: __turbopack_export_namespace__, c: __turbopack_cache__, M: __turbopack_modules__, l: __turbopack_load__, j: __turbopack_dynamic__, P: __turbopack_resolve_absolute_path__, U: __turbopack_relative_url__, R: __turbopack_resolve_module_id_path__, b: __turbopack_worker_blob_url__, g: global, __dirname, x: __turbopack_external_require__, y: __turbopack_external_import__, z: require } = __turbopack_context__;
{
__turbopack_esm__({
    "POST": (()=>POST)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_import__("[project]/node_modules/next/server.js [app-route] (ecmascript)");
;
async function POST(req) {
    try {
        const { text } = await req.json();
        if (!text || typeof text !== 'string') {
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                error: 'Invalid text'
            }, {
                status: 400
            });
        }
        const headerKey = req.headers.get('x-gemini-api-key');
        const apiKey = headerKey || process.env.GEMINI_API_KEY;
        if (!apiKey) {
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                error: 'Gemini API key missing'
            }, {
                status: 400
            });
        }
        const base = 'https://generativelanguage.googleapis.com/v1beta';
        const key = encodeURIComponent(apiKey);
        const pickModel = async ()=>{
            const preferred = [
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'gemini-1.0-pro'
            ];
            try {
                const listUrl = `${base}/models?key=${key}`;
                const listRes = await fetch(listUrl);
                if (!listRes.ok) return preferred[0];
                const listJson = await listRes.json();
                const models = Array.isArray(listJson?.models) ? listJson.models : [];
                for (const id of preferred){
                    const found = models.find((m)=>typeof m?.name === 'string' && m.name.endsWith(`/models/${id}`));
                    if (found && Array.isArray(found?.supportedGenerationMethods)) {
                        if (found.supportedGenerationMethods.includes('generateContent')) return id;
                    }
                }
                // fallback: first model that supports generateContent
                const anyModel = models.find((m)=>Array.isArray(m?.supportedGenerationMethods) && m.supportedGenerationMethods.includes('generateContent'));
                if (anyModel?.name && typeof anyModel.name === 'string') {
                    return anyModel.name.split('/').pop() || preferred[0];
                }
                return preferred[0];
            } catch  {
                return preferred[0];
            }
        };
        const modelId = await pickModel();
        const url = `${base}/models/${encodeURIComponent(modelId)}:generateContent?key=${key}`;
        const prompt = 'You are a real-time speech/text post-processor. Convert the given noisy letter-by-letter transcript into correct English words.\n' + 'Rules:\n' + '- Return ONLY the corrected text (no quotes, no markdown).\n' + '- Keep it short.\n' + '- If it is already correct, return it unchanged.\n' + '- Do not add extra words that are not implied.\n' + `Input: ${text}`;
        const geminiRes = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contents: [
                    {
                        role: 'user',
                        parts: [
                            {
                                text: prompt
                            }
                        ]
                    }
                ],
                generationConfig: {
                    temperature: 0.2,
                    maxOutputTokens: 64
                }
            })
        });
        if (!geminiRes.ok) {
            const errText = await geminiRes.text();
            let retryAfterSeconds;
            try {
                const parsed = JSON.parse(errText);
                const details = parsed?.error?.details;
                if (Array.isArray(details)) {
                    const retryInfo = details.find((d)=>d?.['@type'] === 'type.googleapis.com/google.rpc.RetryInfo');
                    const delay = retryInfo?.retryDelay;
                    if (typeof delay === 'string') {
                        const m = delay.match(/(\d+)/);
                        if (m) retryAfterSeconds = Number(m[1]);
                    }
                }
            } catch  {
            // ignore
            }
            const headerRetryAfter = geminiRes.headers.get('retry-after');
            if (!retryAfterSeconds && headerRetryAfter) {
                const n = Number(headerRetryAfter);
                if (!Number.isNaN(n)) retryAfterSeconds = n;
            }
            const res = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                error: 'Gemini request failed',
                geminiStatus: geminiRes.status,
                geminiBody: errText,
                retryAfterSeconds
            }, {
                status: geminiRes.status
            });
            if (retryAfterSeconds && Number.isFinite(retryAfterSeconds)) {
                res.headers.set('Retry-After', String(Math.max(1, Math.floor(retryAfterSeconds))));
            }
            return res;
        }
        const geminiJson = await geminiRes.json();
        const correctedText = geminiJson?.candidates?.[0]?.content?.parts?.[0]?.text;
        // Gemini can return no candidates/content (e.g. safety block, empty output). In that case,
        // fall back to the original text so the pipeline can continue.
        if (!correctedText || typeof correctedText !== 'string') {
            const finishReason = geminiJson?.candidates?.[0]?.finishReason;
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                correctedText: text.trim(),
                geminiEmpty: true,
                finishReason
            });
        }
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            correctedText: correctedText.trim()
        });
    } catch (err) {
        console.error('Gemini error:', err);
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: 'Internal server error'
        }, {
            status: 500
        });
    }
}
}}),
"[project]/apps/web (server-utils)": ((__turbopack_context__) => {

var { r: __turbopack_require__, f: __turbopack_module_context__, i: __turbopack_import__, s: __turbopack_esm__, v: __turbopack_export_value__, n: __turbopack_export_namespace__, c: __turbopack_cache__, M: __turbopack_modules__, l: __turbopack_load__, j: __turbopack_dynamic__, P: __turbopack_resolve_absolute_path__, U: __turbopack_relative_url__, R: __turbopack_resolve_module_id_path__, b: __turbopack_worker_blob_url__, g: global, __dirname, t: require } = __turbopack_context__;
{
}}),

};

//# sourceMappingURL=%5Broot%20of%20the%20server%5D__54d756._.js.map