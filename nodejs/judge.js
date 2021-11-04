const { NodeVM } = require('vm2');
const fs = require('fs');
const config = require('./config');

if (process.argv.length < 3) {
    console.log('Usage: node judge.js <source code>');
    process.exit(1);
}
if (fs.existsSync(process.argv[2])) {
    let filestat = fs.statSync(process.argv[2]);
    if (filestat.size > config.settings.maxFileSizeKb*1024) {
        console.log(`File exceeded maximum allowed size ${config.settings.maxFileSizeKb}Kb`);
        process.exit(1);
    }
    const vm = new NodeVM({
        console: 'inherit',
        wasm: false,
        eval: false,
        strict: true,
        require: {
            builtin: config.settings.allowedModules
        },
    });
    vm.runFile(process.argv[2]);
} else {
    console.log('File not found');
    process.exit(1);
}