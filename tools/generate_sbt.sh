echo '#!/bin/bash' >> $1/bin/sbt
echo 'SBT_OPTS="-Xms512M -Xmx1536M -Xss1M -XX:+CMSClassUnloadingEnabled -XX:MaxPermSize=256M"' >> $1/bin/sbt
echo "java \$SBT_OPTS -jar $1/opt/sbt/bin/sbt-launch.jar \"\$@\"" >> $1/bin/sbt
