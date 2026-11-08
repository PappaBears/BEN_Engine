// BEN Engine — bencore — minimal dependency-free JSON writer and flat-object reader.
// The node's protocol (spec/PROTOCOL.md) only needs flat objects plus one level of
// nesting on the way OUT (telemetry "ch"/"raw"), and flat objects on the way IN (cmd).
// Keeping this in-house means the same bytes are produced on ESP32 and on the host.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cmath>
#include <cstdlib>
#include <cctype>

namespace bencore {

// ---------------------------------------------------------------- writer
// Fixed-capacity, no heap. Tracks overflow so callers can detect truncation.
class JsonWriter {
public:
    JsonWriter(char* buf, size_t cap) : buf_(buf), cap_(cap) { if (cap_) buf_[0] = 0; }

    void begin_object()            { raw('{'); first_ = true; need_sep_ = false; }
    void end_object()              { raw('}'); first_ = false; need_sep_ = true; }
    void begin_array()             { raw('['); first_ = true; need_sep_ = false; }
    void end_array()               { raw(']'); first_ = false; need_sep_ = true; }

    void key(const char* k)        { sep(); string_raw(k); raw(':'); first_ = true; need_sep_ = false; }
    void key_object(const char* k) { key(k); begin_object(); }
    void key_array(const char* k)  { key(k); begin_array(); }

    void value_string(const char* s) { sep(); string_raw(s); }
    void value_int(long long v)      { sep(); char t[24]; snprintf(t, sizeof t, "%lld", v); raw_str(t); }
    void value_uint(unsigned long long v) { sep(); char t[24]; snprintf(t, sizeof t, "%llu", v); raw_str(t); }
    void value_bool(bool v)          { sep(); raw_str(v ? "true" : "false"); }
    void value_null()                { sep(); raw_str("null"); }
    // Fixed number of decimals, trailing zeros trimmed ("21.40" -> "21.4", "0.00" -> "0").
    void value_num(double v, int decimals = 3) {
        sep();
        if (std::isnan(v) || std::isinf(v)) { raw_str("null"); return; }
        char t[32];
        snprintf(t, sizeof t, "%.*f", decimals, v);
        if (strchr(t, '.')) {
            size_t n = strlen(t);
            while (n > 0 && t[n - 1] == '0') t[--n] = 0;
            if (n > 0 && t[n - 1] == '.') t[--n] = 0;
        }
        if (strcmp(t, "-0") == 0) { t[0] = '0'; t[1] = 0; }
        raw_str(t);
    }

    void kv(const char* k, const char* s)         { key(k); value_string(s); }
    void kv(const char* k, long long v)           { key(k); value_int(v); }
    void kv(const char* k, int v)                 { key(k); value_int(v); }
    void kv(const char* k, unsigned long long v)  { key(k); value_uint(v); }
    void kv(const char* k, uint32_t v)            { key(k); value_uint(v); }
    void kv(const char* k, bool v)                { key(k); value_bool(v); }
    void kv_num(const char* k, double v, int dec = 3) { key(k); value_num(v, dec); }

    const char* c_str() const { return buf_; }
    size_t length() const { return len_; }
    bool overflowed() const { return overflow_; }

private:
    void sep() {
        if (need_sep_) raw(',');
        need_sep_ = true;
        first_ = false;
    }
    void raw(char c) {
        if (len_ + 1 >= cap_) { overflow_ = true; return; }
        buf_[len_++] = c; buf_[len_] = 0;
    }
    void raw_str(const char* s) { while (*s) raw(*s++); }
    void string_raw(const char* s) {
        raw('"');
        for (; *s; ++s) {
            switch (*s) {
                case '"':  raw('\\'); raw('"'); break;
                case '\\': raw('\\'); raw('\\'); break;
                case '\n': raw('\\'); raw('n'); break;
                case '\r': raw('\\'); raw('r'); break;
                case '\t': raw('\\'); raw('t'); break;
                default:
                    if ((unsigned char)*s < 0x20) { char t[8]; snprintf(t, sizeof t, "\\u%04x", *s); raw_str(t); }
                    else raw(*s);
            }
        }
        raw('"');
    }
    // After begin_object/begin_array the next item needs no comma; after a key the value needs no comma.
    char* buf_; size_t cap_; size_t len_ = 0;
    bool first_ = true; bool need_sep_ = false; bool overflow_ = false;
};

// ---------------------------------------------------------------- flat reader
// Parses one JSON object whose values are strings, numbers, booleans or null.
// Nested objects/arrays are skipped as opaque (their text is retained as a string
// so a caller can hand it to a deeper parser if it ever needs to).
struct JsonField {
    enum Type : uint8_t { NONE, STRING, NUMBER, BOOL, NUL, NESTED };
    char key[24];
    char str[128];     // string value (unescaped) or nested raw text (truncated if long)
    double num;
    bool b;
    Type type;
};

class JsonFlat {
public:
    static constexpr int MAX_FIELDS = 12;

    // Returns true if the text is a well-formed flat object (nested values tolerated).
    bool parse(const char* text, size_t len = 0) {
        n_ = 0; error_ = nullptr;
        if (!text) return fail("null input");
        if (len == 0) len = strlen(text);
        const char* p = text; const char* end = text + len;
        skip_ws(p, end);
        if (p >= end || *p != '{') return fail("expected '{'");
        ++p;
        skip_ws(p, end);
        if (p < end && *p == '}') return true; // empty object
        while (true) {
            skip_ws(p, end);
            if (p >= end || *p != '"') return fail("expected key");
            if (n_ >= MAX_FIELDS) return fail("too many fields");
            JsonField& f = fields_[n_];
            f.type = JsonField::NONE;
            if (!read_string(p, end, f.key, sizeof f.key)) return fail("bad key");
            skip_ws(p, end);
            if (p >= end || *p != ':') return fail("expected ':'");
            ++p;
            skip_ws(p, end);
            if (p >= end) return fail("truncated");
            if (*p == '"') {
                if (!read_string(p, end, f.str, sizeof f.str)) return fail("bad string");
                f.type = JsonField::STRING;
            } else if (*p == '{' || *p == '[') {
                const char* start = p;
                if (!skip_nested(p, end)) return fail("bad nested value");
                size_t n = (size_t)(p - start); if (n >= sizeof f.str) n = sizeof f.str - 1;
                memcpy(f.str, start, n); f.str[n] = 0;
                f.type = JsonField::NESTED;
            } else if (strncmp(p, "true", 4) == 0 && (p + 4 <= end)) {
                f.type = JsonField::BOOL; f.b = true; f.num = 1; p += 4;
            } else if (strncmp(p, "false", 5) == 0 && (p + 5 <= end)) {
                f.type = JsonField::BOOL; f.b = false; f.num = 0; p += 5;
            } else if (strncmp(p, "null", 4) == 0 && (p + 4 <= end)) {
                f.type = JsonField::NUL; p += 4;
            } else {
                char* q = nullptr;
                double v = strtod(p, &q);
                if (q == p) return fail("bad value");
                // strtod accepts things JSON does not (hex, inf, nan): reject them
                for (const char* c = p; c < q; ++c)
                    if (!(isdigit((unsigned char)*c) || *c == '-' || *c == '+' || *c == '.' || *c == 'e' || *c == 'E'))
                        return fail("bad number");
                f.type = JsonField::NUMBER; f.num = v; f.b = v != 0; p = q;
                snprintf(f.str, sizeof f.str, "%g", v);
            }
            ++n_;
            skip_ws(p, end);
            if (p >= end) return fail("truncated");
            if (*p == ',') { ++p; continue; }
            if (*p == '}') { ++p; break; }
            return fail("expected ',' or '}'");
        }
        skip_ws(p, end);
        if (p != end) return fail("trailing data");
        return true;
    }

    const JsonField* get(const char* key) const {
        for (int i = 0; i < n_; ++i) if (strcmp(fields_[i].key, key) == 0) return &fields_[i];
        return nullptr;
    }
    const char* get_str(const char* key, const char* dflt = nullptr) const {
        const JsonField* f = get(key);
        return (f && f->type == JsonField::STRING) ? f->str : dflt;
    }
    bool get_num(const char* key, double& out) const {
        const JsonField* f = get(key);
        if (!f) return false;
        if (f->type == JsonField::NUMBER || f->type == JsonField::BOOL) { out = f->num; return true; }
        return false;
    }
    int count() const { return n_; }
    const char* error() const { return error_ ? error_ : ""; }

private:
    bool fail(const char* why) { error_ = why; return false; }
    static void skip_ws(const char*& p, const char* end) { while (p < end && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) ++p; }
    static bool read_string(const char*& p, const char* end, char* out, size_t cap) {
        if (p >= end || *p != '"') return false;
        ++p; size_t n = 0;
        while (p < end && *p != '"') {
            char c = *p++;
            if (c == '\\') {
                if (p >= end) return false;
                char e = *p++;
                switch (e) {
                    case 'n': c = '\n'; break; case 't': c = '\t'; break; case 'r': c = '\r'; break;
                    case '"': case '\\': case '/': c = e; break;
                    case 'b': c = '\b'; break; case 'f': c = '\f'; break;
                    case 'u': { // keep only Latin-1 subset; others become '?'
                        if (p + 4 > end) return false;
                        unsigned v = 0; for (int i = 0; i < 4; ++i) { char h = *p++; v <<= 4;
                            if (h >= '0' && h <= '9') v |= h - '0'; else if (h >= 'a' && h <= 'f') v |= h - 'a' + 10;
                            else if (h >= 'A' && h <= 'F') v |= h - 'A' + 10; else return false; }
                        c = v < 0x80 ? (char)v : '?'; break; }
                    default: return false;
                }
            }
            if (n + 1 < cap) out[n++] = c;  // silently truncate over-long strings
        }
        if (p >= end) return false;
        ++p; out[n] = 0; return true;
    }
    static bool skip_nested(const char*& p, const char* end) {
        int depth = 0; bool in_str = false;
        while (p < end) {
            char c = *p++;
            if (in_str) { if (c == '\\') { if (p < end) ++p; } else if (c == '"') in_str = false; continue; }
            if (c == '"') in_str = true;
            else if (c == '{' || c == '[') ++depth;
            else if (c == '}' || c == ']') { if (--depth == 0) return true; if (depth < 0) return false; }
        }
        return false;
    }
    JsonField fields_[MAX_FIELDS];
    int n_ = 0; const char* error_ = nullptr;
};

} // namespace bencore
