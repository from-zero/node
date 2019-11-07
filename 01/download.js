module.exports.clone = async function clone(repo, path) {
    const {promisify} = require('util')
    const download = promisify(require('download-git-repo'));
    const ora = require('ora');
    const process = ora('下载项目...');
    process.start();
    try{
        await download(repo, path);
        process.succeed()
    }catch{
        process.fail()
    }
}