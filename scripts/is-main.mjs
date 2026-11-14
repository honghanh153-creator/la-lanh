// Is this module the script node was started with? (lesson L16, 13.11.2026)
// The old check compared import.meta.url with pathToFileURL(process.argv[1]). Node resolves
// symlinks for import.meta.url but not for argv[1], so a script started through a symlinked path
// (or through macOS /var -> /private/var) ran nothing and exited 0: a guard that never ran looked
// like a pass. Both sides are compared after resolving symlinks.
import { realpathSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

export function isMain(url, argv1 = process.argv[1]) {
  if (!argv1) return false;
  try {
    return realpathSync(argv1) === realpathSync(fileURLToPath(url));
  } catch {
    // A path that cannot be resolved: keep the plain comparison, never a silent "not main" for
    // the script that was actually started.
    return url === pathToFileURL(argv1).href;
  }
}
