var QRCode = require('qrcode')

QRCode.toDataURL('4cc959a2-e558-4890-86bd-2031431efc12', function (err, url) {
  console.log(url)
});