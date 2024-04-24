local file_path = debug.getinfo(1, "S").source:sub(2)
local file_dir = file_path:match("(.*[/\\])")
local endpoint_script = file_dir .. "endpoint.py"
local missingMarimoCell = true

-- needs to be unique to process
key = quarto.doc.input_file
function from_endpoint(endpoint, text)
  text = text or ""
  return pandoc.pipe("python", {endpoint_script, key, endpoint}, text)
end

-- Hook functions to pandoc
function CodeBlock(el)
  if el.attr and el.attr.classes:find_if(function (c) return string.match(c, "{?marimo%-key}?") end) then
      missingMarimoCell = false
      cell_output = from_endpoint("lookup", el.text)
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

  -- Don't add assets to non-html documents
  if not quarto.doc.is_format("html") then
    return doc
  end

  quarto.doc.include_text(
      "in-header",
      "<base href='/' />")

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
  assets = from_endpoint("assets")
  quarto.doc.include_text(
    "after-body", assets
  )
  return doc
end