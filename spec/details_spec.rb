require 'spec_helper'

require 'jekyll'
require root_path('_plugins/details.rb')

RSpec.describe Jekyll::Tags::DetailsTag do
  it 'renders summary and body through the markdown converter' do
    converter = instance_double('MarkdownConverter')
    site = instance_double('Site')

    allow(site).to receive(:find_converter_instance).with(Jekyll::Converters::Markdown).and_return(converter)
    allow(converter).to receive(:convert) do |input|
      case input.strip
      when 'Caption *text*'
        "<p>Caption <em>text</em></p>\n"
      when 'Body **content**'
        "<p>Body <strong>content</strong></p>\n"
      else
        input
      end
    end

    template = Liquid::Template.parse('{% details Caption *text* %}Body **content**{% enddetails %}')
    output = template.render({}, registers: { site: site })

    expect(output).to eq('<details><summary>Caption <em>text</em></summary><p>Body <strong>content</strong></p>' \
                         "\n</details>")
  end
end
