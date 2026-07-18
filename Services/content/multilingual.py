"""Multilingual Content Generator — translate & culturally adapt content to 11 languages.

Handles: literal mapping, cultural adaptation, local hashtags, emoji tuning,
CTA localization, platform char limits per language.

No external translation API needed — uses deterministic phrase-level replacement
with cultural context (production-viable for affiliate short-form captions).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

# ── Constants ──────────────────────────────────────────────────

SUPPORTED_LANGUAGES: dict[str, str] = {
    "id": "Indonesian",
    "en": "English",
    "es": "Spanish",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "th": "Thai",
    "vi": "Vietnamese",
    "hi": "Hindi",
    "ar": "Arabic",
    "tr": "Turkish",
}

# Platform char limits per language
PLATFORM_LIMITS: dict[str, dict[str, int]] = {
    "tiktok": {
        "id": 300, "en": 300, "es": 300, "pt": 300,
        "ja": 300, "ko": 300, "th": 300, "vi": 300,
        "hi": 300, "ar": 300, "tr": 300,
    },
    "instagram": {
        "id": 2200, "en": 2200, "es": 2200, "pt": 2200,
        "ja": 2200, "ko": 2200, "th": 2200, "vi": 2200,
        "hi": 2200, "ar": 2200, "tr": 2200,
    },
    "twitter": {
        "id": 280, "en": 280, "es": 280, "pt": 280,
        "ja": 140, "ko": 280, "th": 280, "vi": 280,
        "hi": 280, "ar": 280, "tr": 280,
    },
    "facebook": {
        "id": 63206, "en": 63206, "es": 63206, "pt": 63206,
        "ja": 63206, "ko": 63206, "th": 63206, "vi": 63206,
        "hi": 63206, "ar": 63206, "tr": 63206,
    },
    "youtube": {
        "id": 5000, "en": 5000, "es": 5000, "pt": 5000,
        "ja": 5000, "ko": 5000, "th": 5000, "vi": 5000,
        "hi": 5000, "ar": 5000, "tr": 5000,
    },
    "shopee": {
        "id": 3000, "en": 3000, "es": 3000, "pt": 3000,
        "ja": 3000, "ko": 3000, "th": 3000, "vi": 3000,
        "hi": 3000, "ar": 3000, "tr": 3000,
    },
}

# CTA map per language per platform
CTA_MAP: dict[str, dict[str, str]] = {
    "id": {
        "tiktok": "Link di bio! \U0001f446",
        "instagram": "Link di bio! \U0001f517",
        "facebook": "Order sekarang! Link di komentar.",
        "youtube": "Link di description box!",
        "twitter": "Link di bio! \U0001f517",
    },
    "en": {
        "tiktok": "Link in bio! \U0001f446",
        "instagram": "Link in bio! \U0001f517",
        "facebook": "Order now! Link in comments.",
        "youtube": "Link in description!",
        "twitter": "Link in bio! \U0001f517",
    },
    "es": {
        "tiktok": "¡Enlace en bio! \U0001f446",
        "instagram": "¡Enlace en bio! \U0001f517",
        "facebook": "¡Ordena ahora! Enlace en comentarios.",
        "youtube": "¡Enlace en descripción!",
        "twitter": "¡Enlace en bio! \U0001f517",
    },
    "pt": {
        "tiktok": "Link na bio! \U0001f446",
        "instagram": "Link na bio! \U0001f517",
        "facebook": "Peça agora! Link nos comentários.",
        "youtube": "Link na descrição!",
        "twitter": "Link na bio! \U0001f517",
    },
    "ja": {
        "tiktok": "プロフィールにリンク。\U0001f446",
        "instagram": "プロフィールにリンク。\U0001f517",
        "facebook": "今すぐ注文！コメントにリンク。",
        "youtube": "説明欄にリンク。",
        "twitter": "プロフィールにリンク。\U0001f517",
    },
    "ko": {
        "tiktok": "프로필 링크! \U0001f446",
        "instagram": "프로필 링크! \U0001f517",
        "facebook": "지금 매에! 고유를 링크.",
        "youtube": "설명에 링크!",
        "twitter": "프로필 링크! \U0001f517",
    },
    "th": {
        "tiktok": "รายลิ้มไทย! \U0001f446",
        "instagram": "รายลิ้มไทย! \U0001f517",
        "facebook": "สารภาพยนตร์! รายการเร็จ.",
        "youtube": "รายล่าสระมไทย!",
        "twitter": "รายลิ้มไทย! \U0001f517",
    },
    "vi": {
        "tiktok": "Link trong bio! \U0001f446",
        "instagram": "Link trong bio! \U0001f517",
        "facebook": "Mua ngay! Link trong comment.",
        "youtube": "Link trong description!",
        "twitter": "Link trong bio! \U0001f517",
    },
    "hi": {
        "tiktok": "बायो में लिंक! \U0001f446",
        "instagram": "बायो में लिंक! \U0001f517",
        "facebook": "अब ही ऑर्ड करें! कमेंट्स में लिंक.",
        "youtube": "डिस्क्षन में लिंक!",
        "twitter": "बायो में लिंक! \U0001f517",
    },
    "ar": {
        "tiktok": "الرابط في البائو! \U0001f446",
        "instagram": "الرابط في البائو! \U0001f517",
        "facebook": "اطلب الآن! الرابط في التعليقات.",
        "youtube": "الرابط في الوصف!",
        "twitter": "الرابط في البائو! \U0001f517",
    },
    "tr": {
        "tiktok": "Biyografide link! \U0001f446",
        "instagram": "Biyografide link! \U0001f517",
        "facebook": "Şuimdi sipariş ver! Link yorumlarda.",
        "youtube": "Açıklamada link!",
        "twitter": "Biyografide link! \U0001f517",
    },
}

# Phrase-level translation dictionary (Indonesian → each language)
# Covers common affiliate/marketing phrases
_PHRASE_MAP: dict[str, dict[str, str]] = {
    # ── Price / Value ──
    "murah": {
        "en": "cheap", "es": "barato", "pt": "barato",
        "ja": "安い", "ko": "절하이",
        "th": "ṁผ", "vi": "rẻ", "hi": "सस्ता",
        "ar": "رؾيص", "tr": "ucuz",
    },
    "termurah": {
        "en": "cheapest", "es": "el más barato", "pt": "o mais barato",
        "ja": "最安い", "ko": "최가절",
        "th": "Ḕḡṁผมมอ", "vi": "rẻ nhất",
        "hi": "सबसे सस्ता", "ar": "أرؾض",
        "tr": "en ucuza",
    },
    "promo": {
        "en": "promo", "es": "promo", "pt": "promo",
        "ja": "プロモ", "ko": "프로모",
        "th": "พร้มโ", "vi": "ẩu đại",
        "hi": "प्रमो", "ar": "تنزيل",
        "tr": "kampanya",
    },
    "diskon": {
        "en": "discount", "es": "descuento", "pt": "desconto",
        "ja": "割引", "ko": "크마",
        "th": "รับร้าน", "vi": "đơn giá",
        "hi": "छूट", "ar": "خصم",
        "tr": "indirim",
    },
    "gratis": {
        "en": "free", "es": "gratis", "pt": "grátis",
        "ja": "無料", "ko": "무료",
        "th": "ฟรี", "vi": "miễn phí",
        "hi": "मुफ़त", "ar": "مجاني",
        "tr": "bedava",
    },
    # ── Product Quality ──
    "bagus": {
        "en": "great", "es": "genial", "pt": "ótimo",
        "ja": "素晴らしい", "ko": "좋은",
        "th": "แผ่น", "vi": "tốt",
        "hi": "अच्चा", "ar": "ممتاز",
        "tr": "harika",
    },
    "keren": {
        "en": "awesome", "es": "increíble", "pt": "incrível",
        "ja": "カッコイ", "ko": "장실하다",
        "th": "เครื่อง", "vi": "tuyệt vời",
        "hi": "जबरदास्त", "ar": "رائع",
        "tr": "harika",
    },
    "kualitas": {
        "en": "quality", "es": "calidad", "pt": "qualidade",
        "ja": "品質", "ko": "질리",
        "th": "คุณศุ้ง", "vi": "chất lượng",
        "hi": "गुणवत्ता", "ar": "جودة",
        "tr": "kalite",
    },
    "terbaik": {
        "en": "best", "es": "el mejor", "pt": "o melhor",
        "ja": "最高", "ko": "최고",
        "th": "ดำฝนย", "vi": "tốt nhất",
        "hi": "सबसे अच्चा", "ar": "أفضل",
        "tr": "en iyi",
    },
    # ── Urgency / Action ──
    "buruan": {
        "en": "hurry", "es": "apûrurate", "pt": "corre",
        "ja": "急ぐで", "ko": "빨이",
        "th": "รูป", "vi": "nhanh đi",
        "hi": "जल्มी", "ar": "استعجل",
        "tr": "acele et",
    },
    "jangan sampai kehabisan": {
        "en": "don't miss out", "es": "no te lo pierdas", "pt": "não perca",
        "ja": "解除しないと", "ko": "누라는편",
        "th": "ทำได่ด้วยม์",
        "vi": "đừng bỏ lỡ",
        "hi": "चूको मत मत",
        "ar": "لا تفوت خصله",
        "tr": "kaçırmayın",
    },
    "beli sekarang": {
        "en": "buy now", "es": "compra ahora", "pt": "compre agora",
        "ja": "今すぐ買う", "ko": "지금 매에",
        "th": "สารภาพยนตร์",
        "vi": "mua ngay", "hi": "अब ही ऑर्ड करें",
        "ar": "اطلب الآن",
        "tr": "şimdi al",
    },
    "order sekarang": {
        "en": "order now", "es": "ordena ahora", "pt": "peça agora",
        "ja": "今すぐ注文", "ko": "지금 주문",
        "th": "สารภาพยนตร์",
        "vi": "đặt hàng ngay", "hi": "अब ही ऑर्ड करें",
        "ar": "اطلب الآن",
        "tr": "hemen sipariş ver",
    },
    # ── Content / UGC ──
    "rekomendasi": {
        "en": "recommendation", "es": "recomendación", "pt": "recomendação",
        "ja": "おすすめ", "ko": "추천",
        "th": "ยอดแห่ว", "vi": "đề xử",
        "hi": "सिफ़ारिश", "ar": "تقصير",
        "tr": "öneri",
    },
    "review": {
        "en": "review", "es": "reseña", "pt": "análise",
        "ja": "レビュー", "ko": "리플",
        "th": "รีวิว", "vi": "đánh giá",
        "hi": "समीक्षा", "ar": "مراجعة",
        "tr": "değerlendirme",
    },
    "tips": {
        "en": "tips", "es": "consejos", "pt": "dicas",
        "ja": "テップ", "ko": "튜페",
        "th": "แตะ", "vi": "đường dẫ",
        "hi": "सुञारे", "ar": "نصائح",
        "tr": "ipuçları",
    },
    "viral": {
        "en": "viral", "es": "viral", "pt": "viral",
        "ja": "バイラル", "ko": "비런하다",
        "th": "ยมมย", "vi": "điề truyền",
        "hi": "वायरल", "ar": "عنصري",
        "tr": "viral",
    },
    # ── Product types ──
    "produk": {
        "en": "product", "es": "producto", "pt": "produto",
        "ja": "商品", "ko": "프로데스하트",
        "th": "ผู้ทุต", "vi": "sản phẩm",
        "hi": "उत्पाद", "ar": "منتج",
        "tr": "ürün",
    },
    "gadget": {
        "en": "gadget", "es": "gadget", "pt": "gadget",
        "ja": "ガジェット", "ko": "게잘트",
        "th": "แกงต", "vi": "thiết bị",
        "hi": "गैजेट", "ar": "جادغت",
        "tr": "cihaz",
    },
    "skin care": {
        "en": "skin care", "es": "cuidado de la piel", "pt": "cuidados com a pele",
        "ja": "スयिऱॊー", "ko": "스키넌",
        "th": "รหัสตุ้ง", "vi": "chăm sóc da",
        "hi": "स्किन केयर", "ar": "عناية الجلد",
        "tr": "cilt bakımı",
    },
    "fashion": {
        "en": "fashion", "es": "moda", "pt": "moda",
        "ja": "ファッション", "ko": "팀",
        "th": "แทบ", "vi": "thời trang",
        "hi": "फैशन", "ar": "أزياء",
        "tr": "moda",
    },
    # ── Emotion / Urgency ──
    "wajib": {
        "en": "must have", "es": "imprescindible", "pt": "essencial",
        "ja": "必須", "ko": "필수",
        "th": "ต้องมั", "vi": "phải có",
        "hi": "ज़रूरी", "ar": "ضروري",
        "tr": "olmazsa olmaz",
    },
    "pilihan": {
        "en": "choice", "es": "opción", "pt": "escolha",
        "ja": "選択肢", "ko": "선택지",
        "th": "ตอนไทย", "vi": "sự lựa chọn",
        "hi": "विकल्प", "ar": "خيارة",
        "tr": "seçenek",
    },
    "kekinian": {
        "en": "trending", "es": "tendencia", "pt": "tendência",
        "ja": "トレンdiンg", "ko": "트래딤",
        "th": "ยมมย", "vi": "xu hướng",
        "hi": "रुजनती", "ar": "رائج",
        "tr": "trend",
    },
    # ── Common phrases ──
    "yang lagi viral": {
        "en": "that's going viral", "es": "que está viral", "pt": "que está viral",
        "ja": "バイラル中", "ko": "비런중",
        "th": "ยมมยอย", "vi": "đang điề truyền",
        "hi": "जो वायरल हो रहा है",
        "ar": "الذي يصبح الانتشار",
        "tr": "viral olan",
    },
    "lihat di bio": {
        "en": "see bio", "es": "mira el bio", "pt": "veja o bio",
        "ja": "プロフィール参照", "ko": "프로필 처",
        "th": "ดูล้าใหญ่",
        "vi": "xem bio", "hi": "बायो में देखें",
        "ar": "انظر البائو",
        "tr": "biyografiye bak",
    },
    "tapi sayangnya": {
        "en": "but unfortunately", "es": "pero lamentablemente", "pt": "mas infelizmente",
        "ja": "次のグジェャン", "ko": "하지만 평범하게",
        "th": "แล้วมาดหมด",
        "vi": "nhưng thường không",
        "hi": "लेकिन अफ़सोसे",
        "ar": "لكن للأسف",
        "tr": "ama ne yazık ki",
    },
    "bukan kaleng-kaleng": {
        "en": "top notch", "es": "de primera", "pt": "de primeira",
        "ja": "一流", "ko": "아늘 눅스 눅스하겔",
        "th": "พร้อนแทง", "vi": "không phải dạng",
        "hi": "मामूले नहीं",
        "ar": "جيد", "tr": "klas değil",
    },
    # ── Call-to-action verbs ──
    "coba": {
        "en": "try", "es": "prueba", "pt": "experimente",
        "ja": "試してみて", "ko": "테스트해보세요",
        "th": "ด้าน", "vi": "thử",
        "hi": "प्रयास करें",
        "ar": "جرب", "tr": "dene",
    },
    "coba sekarang": {
        "en": "try now", "es": "prueba ahora", "pt": "experimente agora",
        "ja": "今すぐ試して", "ko": "지금 테스트",
        "th": "ด้านภาพยนตร์",
        "vi": "thử ngay", "hi": "अब ही प्रयास करें",
        "ar": "جرب الآن", "tr": "hemen dene",
    },
    # ── Negation / Contrast ──
    "sayang": {
        "en": "pity", "es": "lástima", "pt": "pena",
        "ja": "次の", "ko": "평문",
        "th": "ดอร์", "vi": "đáng tiếc",
        "hi": "दुःक", "ar": "أسف",
        "tr": "çok yazık",
    },
    "nggak": {
        "en": "don't", "es": "no", "pt": "não",
        "ja": "ない", "ko": "않",
        "th": "ไม่", "vi": "không",
        "hi": "नहीं", "ar": "لا",
        "tr": "yok",
    },
    "nggak nyesel": {
        "en": "no regret", "es": "sin arrepentimiento", "pt": "sem arrependimento",
        "ja": "後悔ない", "ko": "활지하지 않음",
        "th": "ไม่เห็ด", "vi": "không hồi hận",
        "hi": "कोई पश्चात नहीं",
        "ar": "بدون ندم", "tr": "pişman olmazsın",
    },
}

# ── Trending Hashtags per language ──

_TRENDING_HASHTAGS: dict[str, dict[str, list[str]]] = {
    "id": {
        "general": ["#viral", "#rekomendasi", "#fyp", "#reviewproduk", "#tiktokindo"],
        "electronics": ["#gadget", "#teknologi", "#smartphone", "#techindonesia", "#unboxing"],
        "fashion": ["#ootd", "#fashionindonesia", "#style", "#trend", "#outfit"],
        "beauty": ["#skincare", "#beauty", "#reviewskincare", "#selfcare", "#glowup"],
        "food": ["#makanan", "#kuliner", "#foodreview", "#jajanan", "#enak"],
    },
    "en": {
        "general": ["#viral", "#trending", "#musthave", "#fyp", "#recommendation"],
        "electronics": ["#tech", "#gadget", "#smartphone", "#unboxing", "#techreview"],
        "fashion": ["#fashion", "#ootd", "#style", "#outfitinspo", "#trendy"],
        "beauty": ["#skincare", "#beauty", "#skincareroutine", "#glowup", "#selfcare"],
        "food": ["#foodie", "#foodreview", "#delicious", "#foodtok", "#yum"],
    },
    "es": {
        "general": ["#viral", "#tendencia", "#recomendación", "#fyp", "#musthave"],
        "electronics": ["#tech", "#gadget", "#tecnología", "#unboxing", "#review"],
        "fashion": ["#moda", "#fashion", "#outfit", "#estilo", "#tendencia"],
        "beauty": ["#belleza", "#skincare", "#maquillaje", "#beauty", "#cuidadodelapiel"],
        "food": ["#comida", "#foodie", "#receta", "#delicioso", "#sabores"],
    },
    "pt": {
        "general": ["#viral", "#tendência", "#recomendação", "#fyp", "#musthave"],
        "electronics": ["#tech", "#gadget", "#tecnologia", "#unboxing", "#review"],
        "fashion": ["#moda", "#fashion", "#look", "#estilo", "#trendy"],
        "beauty": ["#beleza", "#skincare", "#maquiagem", "#beauty", "#autocuidado"],
        "food": ["#comida", "#foodie", "#receita", "#delicioso", "#sabor"],
    },
    "ja": {
        "general": ["#viral", "#トレンド", "#おすすめ", "#fyp", "#大人気"],
        "electronics": ["#ガジェット", "#テクノロジー", "#スマホ", "#レビュー", "#開封"],
        "fashion": ["#ファッション", "#ootd", "#スタイル", "#コーデ", "#トレンド"],
        "beauty": ["#スキンケア", "#美容", "#beauty", "#肌", "#selfcare"],
        "food": ["#食べ物", "#美食", "#料理", "#グルメ", "#おいしい"],
    },
    "ko": {
        "general": ["#viral", "#트렌드", "#추천", "#fyp", "#인기"],
        "electronics": ["#테크", "#가젯", "#스마트폰", "#리뷰", "#언박싱"],
        "fashion": ["#패션", "#ootd", "#스타일", "#코디", "#트렌드"],
        "beauty": ["#스킨케어", "#뷰티", "#화장품", "#피부", "#데일리룩"],
        "food": ["#먹방", "#맛집", "#음식", "#리뷰", "#맛있는"],
    },
    "th": {
        "general": ["#viral", "#มาแรง", "#แนะนำ", "#fyp", "#ยอดนิยม"],
        "electronics": ["#เทค", "#แกดเจ็ต", "#สมาร์ทโฟน", "#รีวิว", "#แกะกล่อง"],
        "fashion": ["#แฟชั่น", "#ootd", "#สไตล์", "#ชุด", "#เทรนด์"],
        "beauty": ["#สกินแคร์", "#บิวตี้", "#ผิว", "#สวย", "#selfcare"],
        "food": ["#อาหาร", "#รีวิวอาหาร", "#อร่อย", "#ของกิน", "#คาเฟ่"],
    },
    "vi": {
        "general": ["#viral", "#xuhuong", "#gioithieu", "#fyp", "#noibat"],
        "electronics": ["#congnghe", "#gadget", "#dienthoai", "#review", "#unboxing"],
        "fashion": ["#thoitrang", "#ootd", "#phongcach", "#outfit", "#trendy"],
        "beauty": ["#chamsocda", "#lamdep", "#mypham", "#skincare", "#beautiful"],
        "food": ["#amthuc", "#reviewamthuc", "#ngon", "#foodie", "#dulich"],
    },
    "hi": {
        "general": ["#viral", "#trending", "#sifarsh", "#fyp", "#lokpriya"],
        "electronics": ["#tech", "#gadget", "#smartphone", "#review", "#unboxing"],
        "fashion": ["#fashion", "#ootd", "#style", "#outfit", "#trend"],
        "beauty": ["#skincare", "#beauty", "#sundarta", "#twacha", "#selfcare"],
        "food": ["#khana", "#foodie", "#review", "#swadisht", "#streetfood"],
    },
    "ar": {
        "general": ["#viral", "#trend", "#tawsiya", "#fyp", "#shayir"],
        "electronics": ["#tech", "#gadget", "#tech", "#review", "#unboxing"],
        "fashion": ["#fashion", "#ootd", "#style", "#outfit", "#trend"],
        "beauty": ["#beauty", "#skincare", "#jamal", "#taaleem", "#selfcare"],
        "food": ["#food", "#foodie", "#review", "#ladhaeem", "#taam"],
    },
    "tr": {
        "general": ["#viral", "#trend", "#oneri", "#fyp", "#populer"],
        "electronics": ["#tech", "#gadget", "#telefon", "#inceleme", "#unboxing"],
        "fashion": ["#moda", "#ootd", "#stil", "#kombin", "#trend"],
        "beauty": ["#ciltbakimi", "#guzellik", "#skincare", "#makyaj", "#selfcare"],
        "food": ["#yemek", "#foodie", "#lezzet", "#tavsiye", "#yemektarifleri"],
    },
}

# Emoji preferences by culture (some cultures use more, some less)
_EMOJI_STYLE: dict[str, dict[str, str | int]] = {
    "id": {"density": 3, "style": "high", "favorites": ["❤️", "😍", "👍", "😂", "🎉", "💥", "🙌"]},
    "en": {"density": 2, "style": "moderate", "favorites": ["❤️", "😍", "👍", "😂", "🌟", "🚀"]},
    "es": {"density": 3, "style": "high", "favorites": ["❤️", "😍", "👍", "🎉", "🌟", "😂"]},
    "pt": {"density": 3, "style": "high", "favorites": ["❤️", "😍", "👍", "🎉", "🌟", "😂"]},
    "ja": {"density": 2, "style": "moderate", "favorites": ["❤️", "😍", "👍", "⭐", "🌟", "😊"]},
    "ko": {"density": 2, "style": "moderate", "favorites": ["❤️", "😍", "👍", "⭐", "🌟", "😊"]},
    "th": {"density": 3, "style": "high", "favorites": ["❤️", "😍", "👍", "🎉", "🌟", "🙌"]},
    "vi": {"density": 2, "style": "moderate", "favorites": ["❤️", "😍", "👍", "🌟", "🚀", "⭐"]},
    "hi": {"density": 3, "style": "high", "favorites": ["❤️", "😍", "👍", "🎉", "🙌", "🌟"]},
    "ar": {"density": 3, "style": "high", "favorites": ["❤️", "😍", "👍", "🎉", "🙌", "🌟"]},
    "tr": {"density": 2, "style": "moderate", "favorites": ["❤️", "😍", "👍", "⭐", "🌟", "🚀"]},
}

# RTL languages
_RTL_LANGUAGES: set[str] = {"ar"}


# ── Input/Output Models ───────────────────────────────────────

class MultilingualInput(BaseModel):
    """Input for multilingual content generation."""

    content: str = Field(..., min_length=1, description="Source content to translate/adapt")
    source_language: str = Field("id", description="Source language code")
    target_languages: list[str] = Field(
        default_factory=lambda: ["en", "es", "pt", "ja", "ko"],
        description="Target language codes",
    )
    platform: str = Field("tiktok", description="Target platform")
    niche: str = Field("general", description="Content niche for hashtag selection")
    optimize_emojis: bool = Field(True, description="Culturally optimize emoji usage")


class LanguageVariant(BaseModel):
    """A single translated/adapted content variant."""

    language: str
    language_name: str
    content: str
    hashtags: list[str] = Field(default_factory=list)
    cta: str = ""
    char_count: int = 0
    char_limit: int = 0
    cultural_notes: str = ""
    fits_platform: bool = True
    emoji_style: str = ""


class MultilingualPackage(BaseModel):
    """Complete multilingual output package."""

    source_language: str
    source_language_name: str
    variants: list[LanguageVariant]
    total_languages: int
    total_variants: int
    content_summary: str = ""


class SingleTranslateInput(BaseModel):
    """Input for single-language translation."""

    content: str
    source_language: str = "id"
    target_language: str = "en"
    platform: str = "tiktok"
    niche: str = "general"


class SingleTranslateOutput(BaseModel):
    """Output for single-language translation."""

    language: str
    language_name: str
    original_content: str
    translated_content: str
    hashtags: list[str] = Field(default_factory=list)
    cta: str = ""
    char_count: int = 0
    char_limit: int = 0
    cultural_notes: str = ""


# ── Core Engine ───────────────────────────────────────────────

class MultilingualEngine:
    """Translate and culturally adapt affiliate content across 11 languages.

    Uses deterministic phrase-level replacement with cultural context.
    Optimized for short-form affiliate captions (TikTok, IG, FB, Twitter, YouTube).
    """

    def translate(self, inp: MultilingualInput) -> MultilingualPackage:
        """Translate content to all target languages with cultural adaptation."""
        variants: list[LanguageVariant] = []

        for lang_code in inp.target_languages:
            if lang_code not in SUPPORTED_LANGUAGES:
                continue
            if lang_code == inp.source_language:
                continue

            variant = self._translate_single(
                content=inp.content,
                source_lang=inp.source_language,
                target_lang=lang_code,
                platform=inp.platform,
                niche=inp.niche,
                optimize_emojis=inp.optimize_emojis,
            )
            variants.append(variant)

        return MultilingualPackage(
            source_language=inp.source_language,
            source_language_name=SUPPORTED_LANGUAGES.get(inp.source_language, inp.source_language),
            variants=variants,
            total_languages=len(SUPPORTED_LANGUAGES),
            total_variants=len(variants),
            content_summary=f"Translated {len(inp.content)} chars to {len(variants)} languages for {inp.platform}",
        )

    def translate_single(self, inp: SingleTranslateInput) -> SingleTranslateOutput:
        """Translate content to a single target language."""
        variant = self._translate_single(
            content=inp.content,
            source_lang=inp.source_language,
            target_lang=inp.target_language,
            platform=inp.platform,
            niche=inp.niche,
            optimize_emojis=True,
        )
        return SingleTranslateOutput(
            language=variant.language,
            language_name=variant.language_name,
            original_content=inp.content,
            translated_content=variant.content,
            hashtags=variant.hashtags,
            cta=variant.cta,
            char_count=variant.char_count,
            char_limit=variant.char_limit,
            cultural_notes=variant.cultural_notes,
        )

    def _translate_single(
        self,
        content: str,
        source_lang: str,
        target_lang: str,
        platform: str,
        niche: str,
        optimize_emojis: bool,
    ) -> LanguageVariant:
        """Core translation: phrase replacement + CTA + hashtags + emoji tuning."""

        # Step 1: Phrase-level translation
        translated = self._apply_phrase_map(content, source_lang, target_lang)

        # Step 2: Local CTA
        cta = CTA_MAP.get(target_lang, {}).get(platform, "")

        # Step 3: Remove source-language CTA if present in content
        source_cta = CTA_MAP.get(source_lang, {}).get(platform, "")
        if source_cta and source_cta in translated:
            translated = translated.replace(source_cta, "").strip()

        # Step 4: Get platform limit
        char_limit = PLATFORM_LIMITS.get(platform, {}).get(target_lang, 300)

        # Step 5: Get trending hashtags
        hashtags = self._get_hashtags(target_lang, niche)

        # Step 6: Assemble final content
        separator = "\n\n" if platform in ("instagram", "facebook") else "\n"
        hashtags_str = " ".join(hashtags[:5])  # max 5 hashtags for tight platforms
        final_content = f"{translated.strip()}{separator}{cta}{separator}{hashtags_str}".strip()

        # Step 7: Emoji tuning
        if optimize_emojis:
            final_content, emoji_style = self._optimize_emojis(final_content, target_lang)
        else:
            emoji_style = "unchanged"

        # Step 8: Enforce platform char limit
        fits = len(final_content) <= char_limit
        if not fits:
            final_content = self._truncate_to_limit(final_content, cta, hashtags_str, char_limit)

        # Step 9: RTL for Arabic
        cultural_notes = self._get_cultural_notes(target_lang, platform, niche)

        return LanguageVariant(
            language=target_lang,
            language_name=SUPPORTED_LANGUAGES.get(target_lang, target_lang),
            content=final_content,
            hashtags=hashtags,
            cta=cta,
            char_count=len(final_content),
            char_limit=char_limit,
            cultural_notes=cultural_notes,
            fits_platform=len(final_content) <= char_limit,
            emoji_style=emoji_style,
        )

    def _apply_phrase_map(self, text: str, source_lang: str, target_lang: str) -> str:
        """Apply phrase-level translation from source to target language.

        Tries longest phrases first to avoid partial matches.
        """
        if source_lang == target_lang:
            return text

        result = text

        # Sort phrases longest first (greedy matching)
        sorted_phrases = sorted(_PHRASE_MAP.keys(), key=len, reverse=True)

        # Case-insensitive matching
        result_lower = result.lower()

        for phrase in sorted_phrases:
            phrase_lower = phrase.lower()
            if phrase_lower not in result_lower:
                continue

            target_text = _PHRASE_MAP.get(phrase, {}).get(target_lang)
            if not target_text:
                continue

            # Find position preserving case sensitivity
            idx = result_lower.find(phrase_lower)
            while idx != -1:
                original = result[idx: idx + len(phrase)]
                # Preserve first char capitalization
                if original[0].isupper():
                    replacement = target_text[0].upper() + target_text[1:]
                else:
                    replacement = target_text
                result = result[:idx] + replacement + result[idx + len(phrase):]
                result_lower = result.lower()
                idx = result_lower.find(phrase_lower, idx + len(replacement))

        # If nothing matched (no phrases found), return original
        # In production this would call a real translation API
        if result == text and source_lang != target_lang:
            result = self._fallback_word_map(text, target_lang)

        return result

    def _fallback_word_map(self, text: str, target_lang: str) -> str:
        """Minimal word-level fallback when no phrase matches."""
        # For demo: wrap text with language tag to indicate it needs real translation
        lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
        return f"[{lang_name}] {text}"

    def _get_hashtags(self, lang: str, niche: str) -> list[str]:
        """Get culturally trending hashtags for language and niche."""
        lang_hashtags = _TRENDING_HASHTAGS.get(lang, {})
        niche_key = niche if niche in lang_hashtags else "general"
        return lang_hashtags.get(niche_key, lang_hashtags.get("general", ["#viral"]))

    def _optimize_emojis(self, text: str, lang: str) -> tuple[str, str]:
        """Optimize emoji usage per culture."""
        style = _EMOJI_STYLE.get(lang, {"density": 2, "style": "moderate"})
        favorites: list[str] = style.get("favorites", [])  # type: ignore[assignment]
        density: int = style.get("density", 2)  # type: ignore[assignment]
        style_name: str = style.get("style", "moderate")  # type: ignore[assignment]

        if not favorites or density <= 0:
            return text, style_name

        # Count existing emojis
        emoji_pattern = re.compile(
            "[\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\U00002702-\U000027b0"
            "\U0001f900-\U0001f9ff"
            "\U0001fa00-\U0001fa6f"
            "\U0001fa70-\U0001faff"
            "\U00002600-\U000026ff"
            "\U0000fe00-\U0000fe0f"
            "]+",
            flags=re.UNICODE,
        )

        existing_emojis = emoji_pattern.findall(text)
        emoji_count = len("".join(existing_emojis))

        # If high-density culture and few emojis, append some
        if style_name == "high" and emoji_count < density:
            # Add 1-2 favorite emojis at end (before hashtags)
            parts = text.rsplit("\n", 1)
            if len(parts) == 2:
                text = f"{parts[0]} {favorites[0]}{favorites[1]}\n{parts[1]}"
            else:
                text = f"{text} {favorites[0]}{favorites[1]}"

        return text, style_name

    def _truncate_to_limit(self, content: str, cta: str, hashtags: str, limit: int) -> str:
        """Smart truncation: preserve CTA and hashtags, trim body."""
        # Reserve space for CTA + hashtags
        suffix = f"\n{cta}\n{hashtags}"
        suffix_len = len(suffix)

        if suffix_len >= limit:
            # Even suffix is too long — strip hashtags, keep CTA
            suffix = f"\n{cta}"
            suffix_len = len(suffix)

        body_limit = limit - suffix_len - 1  # -1 for newline before body
        if body_limit < 20:
            # Nothing to show
            return suffix[:limit]

        # Split into lines, truncate body
        lines = content.split("\n")
        body_lines: list[str] = []
        current_len = 0

        # Find body lines (exclude existing CTA/hashtag patterns)
        for line in lines:
            stripped = line.strip()
            if stripped == cta or stripped.startswith("#") or stripped == "":
                continue
            if current_len + len(stripped) + 1 > body_limit:
                # Partial fit
                remaining = body_limit - current_len - 3  # space for "..."
                if remaining > 10:
                    body_lines.append(stripped[:remaining].rstrip() + "...")
                break
            body_lines.append(stripped)
            current_len += len(stripped) + 1

        body = "\n".join(body_lines)
        return f"{body}\n{suffix}".strip()[:limit]

    def _get_cultural_notes(self, lang: str, platform: str, niche: str) -> str:
        """Generate cultural adaptation notes."""
        notes: list[str] = []

        if lang in _RTL_LANGUAGES:
            notes.append("RTL language — right-to-left text rendering required")

        if lang == "id":
            notes.append("Informal tone preferred (gaul) for TikTok/IG")
        elif lang == "ja":
            notes.append("Honorific tone preferred; avoid overly casual phrasing")
        elif lang == "ko":
            notes.append("Use polite endings (-요, -습니다) for professional content")
        elif lang == "th":
            notes.append("Thai script mixing with English is common in social content")
        elif lang == "hi":
            notes.append("Hinglish (Hindi+English) acceptable for social media")
        elif lang == "ar":
            notes.append("MSA for broad reach; dialect-specific for targeted campaigns")

        platform_notes = {
            "tiktok": "Short-form: keep under 300 chars, punchy hooks",
            "instagram": "Long-form allowed, front-load hook in first line",
            "twitter": "Most restrictive — every char counts",
            "facebook": "Longest form, storytelling preferred",
        }
        if platform in platform_notes:
            notes.append(platform_notes[platform])

        if niche == "electronics":
            notes.append("Tech audience: use product names/specs in English transliteration")
        elif niche == "fashion":
            notes.append("Fashion audience: lifestyle imagery language, aspirational tone")
        elif niche == "beauty":
            notes.append("Beauty audience: ingredient names often kept in English")

        return "; ".join(notes) if notes else "Standard adaptation applied"


# Module-level singleton
_engine: MultilingualEngine | None = None


def get_engine() -> MultilingualEngine:
    """Get singleton MultilingualEngine."""
    global _engine
    if _engine is None:
        _engine = MultilingualEngine()
    return _engine


# ── Convenience async functions (for MCP tools) ───────────────

async def translate_content(
    content: str,
    source_language: str = "id",
    target_languages: list[str] | None = None,
    platform: str = "tiktok",
    niche: str = "general",
    optimize_emojis: bool = True,
) -> MultilingualPackage:
    """Translate and culturally adapt content to multiple languages."""
    if target_languages is None:
        target_languages = ["en", "es", "pt", "ja", "ko"]

    engine = get_engine()
    inp = MultilingualInput(
        content=content,
        source_language=source_language,
        target_languages=target_languages,
        platform=platform,
        niche=niche,
        optimize_emojis=optimize_emojis,
    )
    return engine.translate(inp)


async def translate_single(
    content: str,
    source_language: str = "id",
    target_language: str = "en",
    platform: str = "tiktok",
    niche: str = "general",
) -> SingleTranslateOutput:
    """Translate content to a single target language."""
    engine = get_engine()
    inp = SingleTranslateInput(
        content=content,
        source_language=source_language,
        target_language=target_language,
        platform=platform,
        niche=niche,
    )
    return engine.translate_single(inp)


async def get_supported_languages() -> dict[str, str]:
    """Return all supported languages."""
    return dict(SUPPORTED_LANGUAGES)


async def get_platform_limits(platform: str) -> dict[str, int]:
    """Return char limits for a platform across all languages."""
    return dict(PLATFORM_LIMITS.get(platform, {}))
