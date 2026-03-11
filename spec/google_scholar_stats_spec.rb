require 'spec_helper'

require root_path('_plugins/google-scholar-stats.rb')

RSpec.describe Jekyll::GoogleScholar do
  around do |example|
    Dir.mktmpdir do |dir|
      Dir.chdir(dir) { example.run }
    end
  end

  it 'returns cached stats when the cache entry is fresh' do
    stats = { 'citations' => '10' }.to_json
    described_class.write_cache('abc123', stats)

    expect(described_class.stats_for('abc123')).to eq(stats)
  end

  it 'fetches and writes stats when no cache exists' do
    allow(described_class).to receive(:fetch_scholar_stats).with('abc123').and_return({ 'papers' => '3' }.to_json)

    result = described_class.stats_for('abc123')
    cache = JSON.parse(File.read(Jekyll::GoogleScholar::CACHE_FILE))

    expect(result).to eq({ 'papers' => '3' }.to_json)
    expect(cache.dig('abc123', 'data')).to eq({ 'papers' => '3' }.to_json)
  end

  it 'ignores corrupted cache files' do
    File.write(Jekyll::GoogleScholar::CACHE_FILE, '{not-json')

    expect(described_class.read_cache('abc123')).to be_nil
  end

  it 'rejects blank scholar ids' do
    expect { described_class.stats_for('') }.to raise_error(RuntimeError, /Invalid scholar_id/)
  end
end

RSpec.describe Jekyll::GoogleScholarStat do
  it 'extracts an individual stat from a json payload' do
    tag = described_class.send(:new, 'scholar_stat', 'stats_json citations', Liquid::ParseContext.new)
    context = Liquid::Context.new('stats_json' => { 'citations' => '42' }.to_json)

    expect(tag.render(context)).to eq('42')
  end

  it 'returns N/A when the payload is invalid json' do
    tag = described_class.send(:new, 'scholar_stat', 'stats_json citations', Liquid::ParseContext.new)
    context = Liquid::Context.new('stats_json' => 'not-json')

    expect(tag.render(context)).to eq('N/A')
  end
end
