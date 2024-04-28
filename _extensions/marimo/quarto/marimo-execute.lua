local missingMarimoCell = true
local from_endpoint = require 'marimo-utils'.endpoint_fn(quarto.doc)
local is_mime_sensitive = require 'marimo-utils'.is_mime_sensitive(quarto.doc)

-- Hook functions to pandoc
function CodeBlock(el)
  if el.attr and el.attr.classes:find_if(function (c) return string.match(c, "{?marimo%-key}?") end) then
      missingMarimoCell = false
      cell_output = from_endpoint("lookup", el.text)
      cell_table = quarto.json.decode(cell_output)

      -- A type will be returned if the output type is mime sensitive (e.g. pdf,
      -- or latex).
      if is_mime_sensitive then
        local response = {} -- empty
        if cell_table.display_code then
          table.insert(response, pandoc.CodeBlock(cell_table.code, "python"))
        end

        if cell_table.type == "figure" then
          -- for latex/pdf, has to be run with --extract-media=media flag
          -- can also set this in qmd header
          image = pandoc.Image("Generated Figure", cell_table.value)
          table.insert(response, pandoc.Figure(pandoc.Para{image}))
          return response
        end
        if cell_table.type == "para" then
          table.insert(response, pandoc.Para(cell_table.value))
          return response
        end
        if cell_table.type == "blockquote" then
          table.insert(response, pandoc.BlockQuote(cell_table.value))
          return response
        end
        local code_block = response[1]
        response = pandoc.read(cell_table.value, cell_table.type).blocks
        table.insert(response, code_block)
        return response
      end

      return pandoc.RawBlock(cell_table.type, cell_table.value)
  end
end


function Pandoc(doc)

  -- Don't do anything if we don't have to
  if missingMarimoCell then
    return doc
  end

  -- Don't add assets to non-html documents
  if not quarto.doc.is_format("html") then
    from_endpoint("flush")
    return doc
  end

  -- For local testing we can connect to the frontend webserver
  local dev_server = os.getenv("QUARTO_MARIMO_DEBUG_ENDPOINT")
  if dev_server ~= nil then
    quarto.doc.include_text(
      "in-header",
      '<meta name="referrer" content="unsafe-url" />' ..
      '<script type="module" crossorigin="anonymous">import { injectIntoGlobalHook } from "' .. dev_server ..
      '/@react-refresh";injectIntoGlobalHook(window); window.$RefreshReg$ = () => {};' ..
      'window.$RefreshSig$ = () => (type) => type;</script>' ..
      '<script type="module" crossorigin="anonymous" src="' .. dev_server ..
      '/@vite/client"></script>'
    )
  end

  -- Web assets, seems best way
  assets = from_endpoint("assets-and-flush")
  quarto.doc.include_text(
    "in-header", assets
  )
  return doc
end
