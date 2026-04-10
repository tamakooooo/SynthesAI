# {{ title }}

**单词数量**: {{ statistics.total_words }}
**生成时间**: {{ created_at.strftime('%Y-%m-%d %H:%M:%S') }}

---

## 📚 单词卡片列表

{% for card in vocabulary_cards %}
### {{ card.word }} {% if card.phonetic.us %}`{{ card.phonetic.us }}`{% endif %}

**词性**: {{ card.part_of_speech }}

**释义**: {{ card.definition.zh }}

{% if card.definition.en %}
**英文释义**: {{ card.definition.en }}
{% endif %}

**例句**:
{% for example in card.example_sentences %}
- {{ example.sentence }}
  {{ example.translation }}
{% endfor %}

{% if card.synonyms %}
**同义词**: {% for syn in card.synonyms %}{{ syn }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

{% if card.antonyms %}
**反义词**: {% for ant in card.antonyms %}{{ ant }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

{% if card.related_words %}
**相关词**: {% for rel in card.related_words %}{{ rel }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

**难度**: {{ card.difficulty }}
**词频**: {{ card.frequency }}

---

{% endfor %}

{% if context_story %}
## 📖 上下文故事

**标题**: {{ context_story.title }}

{{ context_story.content }}

**目标单词**: {% for word in context_story.target_words %}{{ word }}{% if not loop.last %}, {% endif %}{% endfor %}

---

{% endif %}

## 📊 统计信息

### 难度分布

- **初级**: {{ statistics.difficulty_distribution.beginner }} 词
- **中级**: {{ statistics.difficulty_distribution.intermediate }} 词
- **高级**: {{ statistics.difficulty_distribution.advanced }} 词

### 词频分布

- **高频**: {{ statistics.frequency_distribution.high }} 词
- **中频**: {{ statistics.frequency_distribution.medium }} 词
- **低频**: {{ statistics.frequency_distribution.low }} 词

### 词性分布

{% for pos, count in statistics.part_of_speech_distribution.items() %}
- **{{ pos }}**: {{ count }} 词
{% endfor %}

---

*由 SynthesAI 自动生成*
*学习助手 · 知识综合*