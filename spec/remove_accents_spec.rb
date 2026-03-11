require 'spec_helper'

require root_path('_plugins/remove-accents.rb')

RSpec.describe Jekyll::CleanString do
  it 'transliterates accented text' do
    filter = Object.new.extend(described_class)

    expect(filter.remove_accents('Crème brûlée')).to eq('Creme brulee')
  end
end
