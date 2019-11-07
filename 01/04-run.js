const fs = require('fs')
const path = require('path')

const data = fs.readFileSync('./conf.js')
console.log(data, data.toString())
console.log(path.resolve(path.resolve(__dirname, './conf.js')))

fs.readFile('./conf.js',(err,data)=>{
    if(err) throw err;
    console.log(data)
})
console.log('其他操作')
//promisify
const {promisify} = require('util')
const readFile = promisify(fs.readFile)
readFile('./conf.js').then(data=>console.log(data))

//v10 fs promise
const fsp = require('fs').promises;
const {Buffer} = require('buffer')
const b = Buffer.from('{a:1}')

fsp.writeFile('./conf.js',b).then(data=>console.log('write'+data));
fsp.readFile('./conf.js').then(data=>console.log(data,data.toString()))

;(async()=>{
    const fsp = require('fs').promises;
    const d = await fsp.readFile('./test.js')
    console.log(d.toString('utf-8'))
})()