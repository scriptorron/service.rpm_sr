
rm -frd build

mkdir -p build/service.rpm_sr

cp -R resources build/service.rpm_sr
cp addon.xml build/service.rpm_sr
cp default.py build/service.rpm_sr
cp service.py build/service.rpm_sr
cp README.md build/service.rpm_sr

cd build
zip -r service.rpm_sr.zip service.rpm_sr
mv -f service.rpm_sr.zip ..
cd ..

rm -frd build
