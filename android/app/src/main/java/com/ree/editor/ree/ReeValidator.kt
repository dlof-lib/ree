package com.ree.editor.ree

/**
 * مدقق خفيف يعمل على الجهاز مباشرة (بدون تشغيل فعلي):
 * - يتحقق من توازن الأقواس {} [] ()
 * - يتحقق من أن كل كتلة رئيسية من الأدوار المعروفة
 * التنفيذ الفعلي (توليد الملفات/التشفير/الضغط) يتم عبر محرك REE بلغة بايثون.
 */
object ReeValidator {

    private val KNOWN_ROLES = setOf("REE", "meta", "ext", "path", "crypt", "zip", "img")

    data class Result(val isValid: Boolean, val message: String)

    fun validate(source: String): Result {
        val stack = ArrayDeque<Char>()
        val pairs = mapOf('}' to '{', ']' to '[', ')' to '(')

        var inString = false
        var i = 0
        while (i < source.length) {
            val c = source[i]
            if (c == '"' && (i == 0 || source[i - 1] != '\\')) {
                inString = !inString
            } else if (!inString) {
                when (c) {
                    '{', '[', '(' -> stack.addLast(c)
                    '}', ']', ')' -> {
                        if (stack.isEmpty() || stack.removeLast() != pairs[c]) {
                            return Result(false, "❌ خطأ في توازن الأقواس عند الموضع $i")
                        }
                    }
                }
            }
            i++
        }
        if (stack.isNotEmpty()) {
            return Result(false, "❌ يوجد قوس غير مغلق: '${stack.last()}'")
        }
        if (inString) {
            return Result(false, "❌ سلسلة نصية غير مغلقة")
        }

        val roleRegex = Regex("""(\w+)\s*\{""")
        val foundRoles = roleRegex.findAll(source).map { it.groupValues[1] }.toList()
        val unknown = foundRoles.filter { it !in KNOWN_ROLES }
        if (unknown.isNotEmpty()) {
            return Result(false, "⚠️ أدوار غير معروفة: ${unknown.joinToString()}")
        }
        if (foundRoles.none { it == "ext" || it == "path" || it == "crypt" || it == "zip" || it == "img" }) {
            return Result(false, "⚠️ لا توجد أي كتلة فعّالة (ext/path/crypt/zip/img)")
        }

        return Result(true, "✅ الصياغة سليمة (${foundRoles.size} كتلة)")
    }
}
