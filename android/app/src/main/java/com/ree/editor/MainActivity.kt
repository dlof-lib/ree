package com.ree.editor

import android.net.Uri
import android.os.Bundle
import android.text.Editable
import android.text.SpannableString
import android.text.Spanned
import android.text.TextWatcher
import android.text.style.ForegroundColorSpan
import android.text.style.StyleSpan
import android.graphics.Typeface
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.ree.editor.databinding.ActivityMainBinding
import com.ree.editor.ree.ReeValidator

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var currentUri: Uri? = null
    private var highlighting = false

    private val openLauncher =
        registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
            uri ?: return@registerForActivityResult
            currentUri = uri
            val text = contentResolver.openInputStream(uri)?.bufferedReader()?.readText().orEmpty()
            binding.editorText.setText(text)
            toast("تم فتح الملف")
        }

    private val createLauncher =
        registerForActivityResult(ActivityResultContracts.CreateDocument("text/plain")) { uri ->
            uri ?: return@registerForActivityResult
            currentUri = uri
            saveToUri(uri)
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setSupportActionBar(binding.toolbar)

        binding.editorText.setText(DEFAULT_SAMPLE)
        applyHighlighting(binding.editorText.text)

        binding.editorText.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
            override fun onTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
            override fun afterTextChanged(s: Editable?) {
                if (highlighting || s == null) return
                applyHighlighting(s)
            }
        })

        binding.btnOpen.setOnClickListener {
            openLauncher.launch(arrayOf("*/*"))
        }

        binding.btnSave.setOnClickListener {
            val uri = currentUri
            if (uri != null) saveToUri(uri)
            else createLauncher.launch("untitled.ree")
        }

        binding.btnValidate.setOnClickListener {
            val result = ReeValidator.validate(binding.editorText.text.toString())
            binding.statusText.text = result.message
            binding.statusText.setTextColor(
                if (result.isValid) 0xFF2E7D32.toInt() else 0xFFC62828.toInt()
            )
        }
    }

    private fun saveToUri(uri: Uri) {
        contentResolver.openOutputStream(uri)?.use { out ->
            out.write(binding.editorText.text.toString().toByteArray())
        }
        toast("تم الحفظ")
    }

    private fun toast(msg: String) = Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()

    /** تلوين بسيط للكلمات المفتاحية والسلاسل النصية والتعليقات داخل المحرر. */
    private fun applyHighlighting(editable: Editable) {
        highlighting = true
        val text = editable.toString()
        val spannable = SpannableString(text)

        val keywords = listOf(
            "REE", "meta", "ext", "path", "crypt", "zip", "img",
            "let", "if", "else", "for", "in", "define", "import",
            "true", "false", "null",
        )
        for (kw in keywords) {
            var idx = text.indexOf(kw)
            while (idx >= 0) {
                val boundaryOk = (idx == 0 || !text[idx - 1].isLetterOrDigit()) &&
                        (idx + kw.length >= text.length || !text[idx + kw.length].isLetterOrDigit())
                if (boundaryOk) {
                    spannable.setSpan(ForegroundColorSpan(0xFF0E5265.toInt()), idx, idx + kw.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                    spannable.setSpan(StyleSpan(Typeface.BOLD), idx, idx + kw.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                }
                idx = text.indexOf(kw, idx + 1)
            }
        }

        Regex("\"[^\"]*\"").findAll(text).forEach { m ->
            spannable.setSpan(ForegroundColorSpan(0xFF2E7D32.toInt()), m.range.first, m.range.last + 1, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        }

        Regex("//.*").findAll(text).forEach { m ->
            spannable.setSpan(ForegroundColorSpan(0xFF9E9E9E.toInt()), m.range.first, m.range.last + 1, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        }

        val selection = binding.editorText.selectionStart
        binding.editorText.text = spannable.let { android.text.SpannableStringBuilder(it) }
        if (selection in 0..binding.editorText.text.length) {
            binding.editorText.setSelection(selection)
        }
        highlighting = false
    }

    companion object {
        private const val DEFAULT_SAMPLE = """REE {
  meta {
    name: "project-x"
    version: "1.0"
  }

  ext {
    base: "config"
    rule: sequence(".v{n}", n: 1..3)
  }

  path {
    root: "output"
    segments: ["users", "profile", "config{ext.result}"]
    collision: "none"
  }

  crypt {
    algo: "SHA-256"
    mode: "hash"
    target: path.result
  }

  zip {
    format: "gzip"
    level: 9
    input: path.result
  }
}
"""
    }
}
