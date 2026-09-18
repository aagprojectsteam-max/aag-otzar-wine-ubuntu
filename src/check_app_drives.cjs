'use strict';
// The real component's identified, read-only listDrives export.
const fs=require('fs');
const root='C:\\OtzarApp\\OtzarLocal\\launcher\\bin\\x64\\app\\resources\\app.asar';
require(root+'\\bn.js');
try {
 const native=require(root+'\\build\\win_drive_info.node');
 const drives=native.listDrives();
 fs.writeSync(1,JSON.stringify({event:'original_listDrives',drives})+'\n');
} catch(e) {
 fs.writeSync(1,JSON.stringify({event:'original_listDrives_error',name:e.name,message:e.message})+'\n');
 process.exitCode=2;
}
