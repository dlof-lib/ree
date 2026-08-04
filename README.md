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
pip install -e ".[all,dev]"   # يثبت cryptography + Pillow + brotli + zstandard + pytest
ree run examples/example.ree -v
ree run examples/advanced.ree -v
ree check examples/advanced.ree     # تحقق نحوي فقط دون تنفيذ
ree repl                            # وضع تفاعلي
python -m pytest                    # تشغيل الاختبارات
```

الكتل المدعومة أصلًا: `meta{}` `ext{}` `path{}` `crypt{}` `zip{}` `img{}`.
كل كتلة تنتج `blockname.result` يمكن استخدامه في الكتل التالية عبر `blockname.result`
(أو `{blockname.result}` داخل سلسلة نصية للاستيفاء).

### مثال مصغّر
```ree
REE {
  ext  { base: "config", rule: sequence(".v{n}", n: 1..3) }
  path { root: "output", segments: ["data", "config{ext.result}"] }
  crypt{ algo: "SHA-256", mode: "hash", target: path.result }
  zip  { format: "gzip", level: 9, input: path.result }
}
```

## 1.1 ميزات اللغة المتقدمة (الإصدار 0.2)

المحرك الآن مفسّر شجرة-تركيب كامل، وليس مجرد قوالب. يدعم:

- **تعبيرات كاملة**: حسابية `+ - * / %`، منطقية `&& || !`، مقارنة `== != < > <= >=`،
  بترتيب أسبقية صحيح، وأقواس `()` للتجميع.
- **متغيرات**: `let name = expr`.
- **شروط**: `if (cond) { ... } else { ... }` — ما يُعرَّف داخل الفرع يُدمج في النطاق
  الخارجي، فيمكن استخدامه في الكتل اللاحقة.
- **حلقات**: `for x in [a, b, c] { ... }` أو `for n in 1..5 { ... }` — تُنفَّذ الكتلة
  الداخلية لكل عنصر؛ نتيجة آخر تكرار تبقى متاحة بعد الحلقة.
- **دوال معرّفة**: `define name(params) { expr }` تُستدعى كأي دالة أخرى.
- **استيراد**: `import "shared.ree"` يدمج تعريفات ملف آخر (متغيرات ودوال) في النطاق
  الحالي، مع حماية من الاستيراد الدائري.
- **أنواع قيم إضافية**: أعداد عشرية، `true` / `false` / `null`.
- **دوال مكتبة قياسية أوسع**: `env()` `date()` `now()` `uuid()` `sequence()`
  `random()` `hash()` `derive()` `upper()` `lower()` `concat()` `length()`
  `min()` `max()` `round()` `str()` `int()`.
- **رسائل خطأ احترافية** بموقع دقيق (سطر/عمود) ومقتطف من الشيفرة مع مؤشر `^`،
  عبر تسلسل استثناءات موحّد `LexError` / `ParseError` / `EngineError` في
  `ree_lang/errors.py`.
- **كتل قابلة للتوسعة**: أي طرف خارجي يمكنه تسجيل نوع كتلة جديد دون تعديل الحزمة:

```python
from ree_lang.blocks import register_block

@register_block("notify")
def run_notify(props: dict, ctx: dict) -> dict:
    return {"result": f"sent: {props.get('message')}"}
```

انظر `examples/advanced.ree` لمثال يجمع كل هذه الميزات معًا.

## 2. تطبيق محرر REE للموبايل (Kotlin/XML)

تطبيق أندرويد بسيط:
- محرر نصوص مع تلوين تركيبي (Syntax Highlighting) للكلمات المفتاحية `REE ext path crypt zip img` وكلمات التحكم `let if else for in define import`.
- فتح/حفظ ملفات `.ree` عبر Storage Access Framework.
- زر **تحقق** يشغّل مدقق نحوي خفيف على الجهاز (`ReeValidator.kt`) يتأكد من توازن الأقواس، ويستثني كلمات اللغة المفتاحية من فحص "الأدوار"، ويسمح بكتل مخصّصة غير معروفة محليًا (لأنها قد تكون مسجّلة عبر `register_block` في بايثون) — التنفيذ الفعلي (المتغيرات/الشروط/الحلقات/الدوال/توليد الملفات/التشفير/الضغط) يتم عبر محرك بايثون المتقدم.

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
