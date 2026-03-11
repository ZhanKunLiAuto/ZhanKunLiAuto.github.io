require 'date'
require 'spec_helper'
require 'time'

require root_path('_plugins/external-posts.rb')

RSpec.describe ExternalPosts::ExternalPostsGenerator do
  subject(:generator) { described_class.new }

  describe '#parse_published_date' do
    it 'parses string timestamps to utc' do
      parsed = generator.parse_published_date('2024-02-03 10:30:00 +0800')

      expect(parsed).to eq(Time.utc(2024, 2, 3, 2, 30, 0))
    end

    it 'converts date objects to utc time' do
      parsed = generator.parse_published_date(Date.new(2024, 2, 3))

      expect(parsed.utc?).to be(true)
      expect(parsed).to eq(Date.new(2024, 2, 3).to_time.utc)
    end

    it 'rejects unsupported values' do
      expect { generator.parse_published_date(123) }.to raise_error(RuntimeError, /Invalid date format/)
    end
  end

  describe '#fetch_content_from_url' do
    it 'extracts title, summary, and concatenated paragraph text' do
      html = <<~HTML
        <html>
          <head>
            <title>Example Title</title>
            <meta property="og:description" content="Short summary">
          </head>
          <body>
            <p>First paragraph.</p>
            <p>Second paragraph.</p>
          </body>
        </html>
      HTML

      response = instance_double('HTTParty::Response', body: html)
      allow(HTTParty).to receive(:get).with('https://example.com/post').and_return(response)

      content = generator.fetch_content_from_url('https://example.com/post')

      expect(content).to eq(
        title: 'Example Title',
        content: 'First paragraph.Second paragraph.',
        summary: 'Short summary'
      )
    end
  end

  describe '#create_document' do
    it 'falls back to the source name when the title slug is blank' do
      fake_document = Class.new do
        attr_reader :path, :options
        attr_accessor :data, :content

        def initialize(path, options)
          @path = path
          @options = options
          @data = {}
          @content = nil
        end
      end
      stub_const('Jekyll::Document', fake_document)

      posts_collection = Struct.new(:docs).new([])
      site = instance_double('Site', collections: { 'posts' => posts_collection })
      allow(site).to receive(:in_source_dir) { |relative| File.join('/tmp/site', relative) }

      generator.create_document(
        site,
        'My Source',
        'https://example.com/posts/entry-1',
        title: '   ',
        content: 'Post body',
        summary: 'Post summary',
        published: Time.utc(2024, 1, 1)
      )

      doc = posts_collection.docs.first
      expect(doc.path).to eq('/tmp/site/_posts/my-source-entry-1.md')
      expect(doc.data).to include(
        'external_source' => 'My Source',
        'title' => '   ',
        'description' => 'Post summary',
        'redirect' => 'https://example.com/posts/entry-1'
      )
      expect(doc.content).to eq('Post body')
    end
  end
end
