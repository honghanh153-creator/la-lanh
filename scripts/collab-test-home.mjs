// Imported first by collab tests that do not set their own home: every state path (beats, pending
// alerts, logs, locks) resolves to a fresh temp dir, never the owner's ~/.cache/la-lanh-collab.
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-test-'));
