# setup the environment
module list
module load controls
module load pylint
module list
export PYTHONPATH=$PYTHONPATH:${WORKSPACE}/

# Explicitly set the shell to continue if an step fails
# this is required because pylint has a non-zero return code if there 
# are any issues (see pylint --long-help)
set +e

# create a working dir for the logfile/images
mkdir logs

# run tests
nosetests --with-xunit --xunit-file=${WORKSPACE}/logs/nosetests.xml

# run pylint
touch ${WORKSPACE}/__init__.py
pylint --rcfile=${WORKSPACE}/pylintrc ${WORKSPACE}/ > ${WORKSPACE}/logs/pylint.log
echo "Pylint exited with code $?" 
# explicitly butcher the logfile to have WORKSPACE relative paths, not absolute
# to support Jenkins click-though to sourcecode
sed -i s#${WORKSPACE}/## ${WORKSPACE}/logs/pylint.log

