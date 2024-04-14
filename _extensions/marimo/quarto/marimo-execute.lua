local file_path = debug.getinfo(1, "S").source:sub(2)
local file_dir = file_path:match("(.*[/\\])")
local endpoint_script = file_dir .. "endpoint.py"
local missingMarimoCell = true


function CodeBlock(el)
  if el.attr and el.attr.classes:find_if(function (c) return string.match(c, "{?marimo%-key}?") end) then
      missingMarimoCell = false
      cell_output = pandoc.pipe("python", {endpoint_script, "lookup"}, el.text)
      cell_table = quarto.json.decode(cell_output)
      if cell_table.type == "figure" then
        -- for latex/pdf, has to be run with --extract-media=media flag
        -- can also set this in qmd header
        image = pandoc.Image("Generated Figure", cell_table.value)
        return pandoc.Figure(pandoc.Para{image})
      end
      return pandoc.RawBlock(cell_table.type, cell_table.value)
  end
end


function Pandoc(doc)

  -- Don't do anything if we don't have to
  if missingMarimoCell then
    return doc
  end
  -- Flush the endpoint such that dupe cells are not registered
  pandoc.pipe("python", {endpoint_script, "flush"}, "")

  -- Don't add assets to non-html documents
  if not quarto.doc.is_format("html") then
    return doc
  end

  -- For local testing we can connect to the frontend webserver
  local dev_server = os.getenv("QUARTO_MARIMO_DEBUG_ENDPOINT")
  if dev_server ~= nil then
    quarto.doc.include_text(
      "in-header",
      '<script type="module">import { injectIntoGlobalHook } from "' .. dev_server ..
      '/@react-refresh";injectIntoGlobalHook(window); window.$RefreshReg$ = () => {};' ..
      'window.$RefreshSig$ = () => (type) => type;</script>' ..
      '<script type="module" src="' .. dev_server ..
      '/@vite/client"></script>'
    )
  end

  -- Web assets, seems best way
  assets = pandoc.pipe("python", {endpoint_script, "assets"}, "")
  quarto.doc.include_text(
    "after-body", assets
  )
  return doc
end
