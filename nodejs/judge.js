const { NodeVM } = require('vm2');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const fs = require('fs');
const config = require('./config');
const argv = yargs(hideBin(process.argv)).argv;

if (!argv.file) {
    console.log('Usage: node judge.js --file=<source code path>');
    process.exit(1);
}
if (fs.existsSync(argv.file)) {
    let filestat = fs.statSync(argv.file);
    if (filestat.size > config.settings.maxFileSizeKb * 1024) {
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
    vm.runFile(argv.file);
} else {
    console.log('File not found');
    process.exit(1);
}