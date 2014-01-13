# acceptance tests deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by)

    task deprecated do
        # Need to install paver dependencies for the commands to work!
        sh("pip install Paver==1.2.1 psutil==1.2.1 lazy==1.1 path.py==3.0.1")

        puts("Task #{deprecated} has been deprecated. Use #{deprecated_by} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(deprecated_by)
        exit
    end
end

deprecated("ws:migrate", "paver ws_migrate")
