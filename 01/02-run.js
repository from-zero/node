const os = require('os')
console.log(os)
const mem = os.freemem()/ os.totalmem() * 100;
console.log('内存占用率'+mem.toFixed(2)+'%')