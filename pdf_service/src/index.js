// CLI entrypoint: JSON payload on stdin -> PDF bytes on stdout.
// Invoked by the Python backend as a subprocess (see quote_emailer/pdf_estimate.py).
// Exit code 0 with PDF on stdout, or non-zero with the error on stderr.

import { generateEstimatePdf } from './estimatePdf';

const chunks = [];
process.stdin.on('data', (c) => chunks.push(c));
process.stdin.on('end', () => {
  try {
    const payload = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    const doc = generateEstimatePdf(payload);
    const bytes = Buffer.from(doc.output('arraybuffer'));
    process.stdout.write(bytes);
  } catch (err) {
    console.error('[pdf_service] ' + (err && err.stack ? err.stack : String(err)));
    process.exit(1);
  }
});
