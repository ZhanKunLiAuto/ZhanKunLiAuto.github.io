require 'fileutils'
require 'json'
require 'liquid'
require 'tmpdir'

ROOT_DIR = File.expand_path('..', __dir__)

def root_path(*parts)
  File.join(ROOT_DIR, *parts)
end

RSpec.configure do |config|
  config.disable_monkey_patching!
  config.expect_with :rspec do |expectations|
    expectations.syntax = :expect
  end
end
