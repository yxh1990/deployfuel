require '/usr/lib/ruby/gems/1.8/gems/systemu-2.5.2/lib/systemu.rb'
cmd ="rsync -v -a -c -r --delete rsync://10.20.0.2:/puppet/2014.2-6.0/modules/ /etc/puppet/modules/"

def run_and_respond(cmd)
    stdout, stderr, exit_code = runcommand(cmd)
    puts stdout
    puts stderr
    puts exit_code
    if exit_code != 0
          puts 'the shell is error'
    end
end

def runcommand(cmd)
        thread = Thread.current
        stdout = ''
        stderr = ''
        status = systemu(cmd, {'stdout' => stdout, 'stderr' => stderr}) do |cid|
          begin
            while(thread.alive?)
              sleep 0.1
            end
            Process.waitpid(cid) if Process.getpgid(cid)
            rescue SystemExit
            rescue Errno::ESRCH
            rescue Errno::ECHILD
            rescue Exception => e
              puts"#{e}"
          end
        end
        [stdout, stderr, status.exitstatus]
end
run_and_respond("echo $(whoami)")
run_and_respond(cmd)