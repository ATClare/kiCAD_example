from pathlib import Path
Import("env")
root = Path(env['PROJECT_DIR'])
html = (root / 'web/index.html').read_text(encoding='utf-8')
assert ')SOILUI"' not in html
(root / 'include/ui.h').write_text('#pragma once\n#include <Arduino.h>\nstatic const char UI[] PROGMEM = R"SOILUI(' + html + ')SOILUI";\n', encoding='utf-8')

