
# Installing Jekyll

# install ruby

`brew install ruby`

Add brew ruby to path:
`export PATH=/usr/local/opt/ruby/bin:$PATH`

Caveats that came up:
```
==> ruby
By default, binaries installed by gem will be placed into:
  /usr/local/lib/ruby/gems/2.6.0/bin

You may want to add this to your PATH.
```
So yeah, add this folder to your PATH.


## Install Jekyll

```
gem install --user-install bundler jekyll
```

Need to add: `export PATH=$HOME/.gem/ruby/2.6.0/bin:$PATH` to .bashrc

## Link bundle to Gemfile and jekyll dependency:

With `bundler` and `jekyll` installed, create a new `Gemfile` to list project dependencies.
Via command line while in the target repository folder, enter
```
bundle init
```

Edit the `Gemfile` and add jekyll as a dependency:
```
gem "jekyll"
```
If desired, this is a good time to enter in a jekyll theme as a gem as well, eg
`gem "jekyll-theme-slate"`


Run bundle to install `jekyll` for your project:
```
bundle
```
Run `bundle update` to resolve any dependency conflicts.


# Run the local jekyll server

```
bundle exec jekyll serve
```
This opens a server at http://localhost:4000


