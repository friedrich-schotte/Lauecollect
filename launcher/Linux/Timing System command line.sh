#!/usr/bin/expect
while {1} {
spawn telnet 172.21.46.207
set timeout -1
expect "login:" {} eof {wait; send_user "Next connection attempt in 10 s... "; sleep 10; continue}
send "root\r"
expect "Password:"
send "root\r"
expect "# "
send "cd /home/timing_system\r"
interact
wait
send_user "Next connection attempt in 10 s... "
sleep 10
}
