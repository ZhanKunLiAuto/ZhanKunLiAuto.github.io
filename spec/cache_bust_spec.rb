require 'digest/md5'
require 'spec_helper'

require root_path('_plugins/cache-bust.rb')

RSpec.describe Jekyll::CacheBust::CacheDigester do
  around do |example|
    Dir.mktmpdir do |dir|
      Dir.chdir(dir) { example.run }
    end
  end

  it 'appends a digest for a single asset file' do
    FileUtils.mkdir_p('assets')
    File.write('assets/app.css', 'body{color:black;}')

    file_name = 'https://example.com/assets/app.css'
    digest = described_class.new(file_name: file_name).digest!

    expect(digest).to eq("#{file_name}?#{Digest::MD5.hexdigest('body{color:black;}')}")
  end

  it 'digests all files from the configured sass directory' do
    FileUtils.mkdir_p('assets/_sass/nested')
    File.write('assets/_sass/base.scss', 'base')
    File.write('assets/_sass/nested/theme.scss', 'theme')

    expected = Digest::MD5.hexdigest(
      Dir[File.join('assets/_sass', '**', '*')].map { |path| File.read(path) unless File.directory?(path) }.join
    )

    filter = Object.new.extend(Jekyll::CacheBust)
    expect(filter.bust_css_cache('/assets/css/main.css')).to eq("/assets/css/main.css?#{expected}")
  end
end
