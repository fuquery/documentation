#!/usr/bin/env ruby
require 'nokogiri'
require 'rouge'
require 'fileutils'
require 'rouge/lexers/cpp'


# Patch C++ lexer to allow $macros
module Rouge
  module Lexers
    class Cpp
      prepend :root do
        rule /[$]\w+/, Name::Constant
      end
    end
  end
end


ENTITY_MAP = {
  '&amp;'   => '&',
  '&curlybr;' => '{',
  '&rcurlybr;' => '}',
  '&lowbar;' => '_',
  '&period;' => '.',
  '&colon;'  => ':',
  '&lsqb;'   => '[',
  '&rsqb;'   => ']',
  '&verbar;' => '|',
  '&sol;'    => '/',
  '&quest;'   => '?',
  '&excl;'    => '!',
  '&num;'     => '#',
  '&dollar;'  => '$',
  '&percnt;'  => '%',
  '&ast;'     => '*',
  '&plus;'    => '+',
  '&equals;'  => '=',
  '&comma;'   => ',',
  '&semi;'    => ';',
  '&quot;'    => '"',
  '&apos;'    => "'",
  '&rcub;'    => '}',
  '&lcub;'    => '{',
# these replacements happen in code blocks some time, just revert them
  '®'         => '(R)', 
  '©'         => '(C)',
}
base_path = ARGV[0] || 'build'

# Dump all Rouge themes and patch them
outdir = File.join(base_path, '_', 'css', 'rouge')
FileUtils.mkdir_p(outdir)

Rouge::Theme.registry.each do |name, theme_class|
  theme = theme_class.new
  css = theme.render

  css_file = File.join(outdir, "#{name}.css")

  # Split CSS into blocks of "selector { body }"
  blocks = css.scan(/([^{]+)\{([^}]*)\}/m)

  # Find the first block where at least one selector is .highlight (or simple child) and has color/bg
  highlight_block = nil
  blocks.each do |selector_text, body|
    selectors = selector_text.split(",").map(&:strip)
    valid = selectors.any? { |s| s.match?(/^\.highlight(\s*\.[\w-]+)?$/) }
    if valid && body =~ /(color|background(?:-color)?)/i
      highlight_block = body
      break
    end
  end

  unless highlight_block
    puts "Skipping #{name}: no valid .highlight block with color/bg"
    File.write(css_file, css)
    next
  end

  fg = highlight_block[/color\s*:\s*([^;]+);/i, 1]&.strip
  bg = highlight_block[/background(?:-color)?\s*:\s*([^;]+);/i, 1]&.strip

  unless fg && bg
    puts "Skipping #{name}: missing fg/bg in .highlight block"
    File.write(css_file, css)
    next
  end

  patch = <<~CSS

    :root {
      --rouge-fg: #{fg};
      --rouge-bg: #{bg};
    }

    .rouge pre {
      background-color: var(--rouge-bg) !important;
      color: var(--rouge-fg);
    }

    .rouge .line { white-space: pre; }
    .rouge .added { background-color: color-mix(in srgb, var(--rouge-bg), green 30%); }
    .rouge .removed { background-color: color-mix(in srgb, var(--rouge-bg), red 30%); }

  CSS

  File.write(css_file, css + patch)
  puts "Wrote #{css_file}"
end


# rehighlight all HTML files

html_files = Dir.glob(File.join(base_path, '**', '*.html'))
html_files.each do |path|
  doc = Nokogiri::HTML(File.read(path))
  changed = false

  doc.css('pre > code').each do |code_node|
    # Combine class and data-lang tokens, normalize
    tokens = (code_node['class'].to_s.split + code_node['data-lang'].to_s.split(/[,\s]/)).map(&:downcase)
    tokens.map!(&:strip)
    tokens.reject!(&:empty?)
    next if tokens.empty?

    # Only enable diff if diff is present AND at least one other token exists
    if tokens.include?('diff') && (tokens - ['diff']).any?
      diff_enabled = true
      # Pick first non-diff token as language for Rouge
      lang = (tokens - ['diff']).first
    else
      diff_enabled = false
      lang = (tokens - ['diff']).first || 'plaintext'
    end

    # Strip any "language-" prefix just in case
    lang = lang.sub(/^language-/, '')

    source_html = code_node.inner_html

    links = []
    source = source_html.gsub(/<a[^>]*class="xref[^"]*"[^>]*>.*?<\/a>/) do |link|
      token = "ROUGE_LINK_#{links.length}"
      ENTITY_MAP.each { |k,v| link.gsub!(k,v) }
      links << link
      token
    end
    source = Nokogiri::HTML.fragment(source).text
    ENTITY_MAP.each { |k,v| source.gsub!(k,v) }

    lexer = Rouge::Lexer.find_fancy(lang, source) || Rouge::Lexers::PlainText.new
    formatter = Rouge::Formatters::HTML.new

    if diff_enabled
      highlighted_html = formatter.format(lexer.lex(source))
      links.each_with_index do |link, i|
        highlighted_html.gsub!("ROUGE_LINK_#{i}", link)
      end

      source_lines = source.lines.map(&:chomp)
      highlighted_lines = highlighted_html.lines.map(&:chomp)

      # normalize line count
      max_lines = [source_lines.length, highlighted_lines.length].max
      source_lines.fill('', source_lines.length...max_lines)
      highlighted_lines.fill('', highlighted_lines.length...max_lines)

      html_lines = highlighted_lines.each_with_index.map do |hline, i|
        src = source_lines[i]
        line_type =
          if src.start_with?('+') then 'added'
          elsif src.start_with?('-') then 'removed'
          else 'unchanged'
          end
        inner = hline.empty? ? "&#8203;" : hline
        "<span class='line #{line_type}'>#{inner}</span>"
      end

      frag = Nokogiri::HTML::DocumentFragment.parse(
        "<div class='rouge'><pre><code class='highlight #{lang}'>#{html_lines.join("\n")}</code></pre></div>"
      )
      code_node.parent.replace(frag)
      changed = true
    else
      highlighted = formatter.format(lexer.lex(source))
      links.each_with_index do |link, i|
        highlighted.gsub!("ROUGE_LINK_#{i}", link)
      end

      frag = Nokogiri::HTML::DocumentFragment.parse(
        "<div class='rouge'><pre><code class='highlight #{lang}'>#{highlighted}</code></pre></div>"
      )
      code_node.parent.replace(frag)
      changed = true
    end
  end

  if changed
    File.write(path, doc.to_html)
    puts "Rehighlighted #{path}"
  end
end


html_files.each do |path|
  content = File.read(path)
  ENTITY_MAP.each { |k,v| content.gsub!(k,v) }
  File.write(path, content)
end