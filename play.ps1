$PI_IP = "192.168.137.205"
$PI_USER = "ovos"
$REMOTE = "/home/ovos/response.mp3"
$LOCAL = ".\response.mp3"

Write-Host "Copiando audio desde la Raspberry Pi..."
scp "${PI_USER}@${PI_IP}:${REMOTE}" $LOCAL

Write-Host "Reproduciendo..."
Start-Process $LOCAL