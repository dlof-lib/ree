# REE — لغة وصفية + تطبيق محرر أندرويد

مشروع كامل من جزأين:

```
ree-project/
├── ree_lang/              ← محرك اللغة REE بلغة Python (parser + engine)
├── examples/example.ree   ← برنامج REE جاهز للتجربة
├── setup.py
├── android/                ← تطبيق محرر Android (Kotlin + XML)
│   ├── app/src/main/java/com/ree/editor/MainActivity.kt
│   ├── app/src/main/java/com/ree/editor/ree/ReeValidator.kt
│   ├── app/src/main/res/layout/activity_main.xml
│   ├── app/src/main/res/values/*.xml
│   ├── app/build.gradle
│   └── build.gradle / settings.gradle
└── .github/workflows/android-build.yml   ← بناء APK تلقائيًا عبر GitHub Actions
```

## 1. تشغيل لغة REE بلغة Python

```bash
cd ree_lang_project
pip install -e ".[all]"     # يثبت cryptography + Pillow + brotli + zstandard (اختياري)
ree run examples/example.ree -v
```

الكتل المدعومة: `meta{}` `ext{}` `path{}` `crypt{}` `zip{}` `img{}`.
كل كتلة تنتج `blockname.result` يمكن استخدامه في الكتل التالية عبر `{blockname.result}`.

### مثال مصغّر
```ree
REE {
  ext  { base: "config", rule: sequence(".v{n}", n: 1..3) }
  path { root: "output", segments: ["data", "config{ext.result}"] }
  crypt{ algo: "SHA-256", mode: "hash", target: path.result }
  zip  { format: "gzip", level: 9, input: path.result }
}
```

## 2. تطبيق محرر REE للموبايل (Kotlin/XML)

تطبيق أندرويد بسيط:
- محرر نصوص مع تلوين تركيبي (Syntax Highlighting) للكلمات المفتاحية `REE ext path crypt zip img`.
- فتح/حفظ ملفات `.ree` عبر Storage Access Framework.
- زر **تحقق** يشغّل مدقق نحوي خفيف على الجهاز (`ReeValidator.kt`) يتأكد من توازن الأقواس وصحة أسماء الكتل — التنفيذ الفعلي (توليد/تشفير/ضغط) يتم عبر محرك بايثون.

### بناء APK محليًا
يتطلب Android Studio (أو Android SDK + JDK 17):
```bash
cd android
./gradlew assembleDebug    # أو gradle assembleDebug إن لم يوجد wrapper
```
الناتج: `android/app/build/outputs/apk/debug/app-debug.apk`

### بناء APK تلقائيًا عبر GitHub Actions
أي `push` إلى فرع `main` يشغّل `.github/workflows/android-build.yml` الذي:
1. يجهّز JDK 17 و Android SDK و Gradle.
2. ينفّذ `gradle assembleDebug` (و `assembleRelease` لفرع main).
3. يرفع ملف الـ APK كـ Artifact قابل للتحميل من صفحة "Actions" في المستودع.

## 3. خطوات النشر على GitHub
```bash
git init
git add .
git commit -m "REE language + Android editor"
git remote add origin <رابط مستودعك>
git push -u origin main
```
بعد الدفع، افتح تبويب **Actions** في GitHub وانتظر اكتمال البناء، ثم حمّل الـ APK من قسم Artifacts.

## ملاحظة
الأيقونة والألوان الحالية (`#0E5265` وقوسا `{}`) مستوحاة من شعار REE المرفق في بداية المحادثة.
