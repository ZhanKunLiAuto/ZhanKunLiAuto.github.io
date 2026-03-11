require 'spec_helper'

require root_path('_plugins/file-exists.rb')

RSpec.describe Jekyll::FileExistsTag do
  it 'checks existence relative to the configured source directory' do
    Dir.mktmpdir do |dir|
      File.write(File.join(dir, 'present.txt'), 'ok')
      site = Struct.new(:config).new({ 'source' => dir })
      context = Liquid::Context.new({}, {}, { site: site })

      tag = described_class.send(:new, 'file_exists', 'present.txt ', Liquid::ParseContext.new)
      expect(tag.render(context)).to eq('true')
    end
  end
end
