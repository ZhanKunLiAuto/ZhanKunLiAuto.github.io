require 'spec_helper'

require root_path('_plugins/hide-custom-bibtex.rb')

RSpec.describe Jekyll::HideCustomBibtex do
  subject(:filter_host) do
    Object.new.tap do |object|
      object.extend(described_class)
      context = Liquid::Context.new({}, {}, { site: Struct.new(:config).new({ 'filtered_bibtex_keywords' => %w[html google_scholar_id] }) })
      object.instance_variable_set(:@context, context)
    end
  end

  it 'removes configured fields and cleans author superscripts' do
    input = <<~BIB
      @misc{paper2024,
        author = {Alice* and Bob†},
        html = {https://example.com},
        google_scholar_id = {gs123},
        title = {Paper Title}
      }
    BIB

    output = filter_host.hideCustomBibtex(input)

    expect(output).to include('author = {Alice and Bob}')
    expect(output).to include('title = {Paper Title}')
    expect(output).not_to include('html =')
    expect(output).not_to include('google_scholar_id =')
    expect(output).not_to include('*')
    expect(output).not_to include('†')
  end
end
