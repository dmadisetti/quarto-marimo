local file_path = debug.getinfo(1, "S").source:sub(2)
local file_dir = file_path:match("(.*[/\\])")
local endpoint_script = file_dir .. "endpoint.py"
local missingMarimoCell = true

function CodeBlock(el)
  if el.attr and el.attr.classes:find_if(function (c) return string.match(c, "{?marimo%-key}?") end) then
      missingMarimoCell = false
      converted_code = pandoc.pipe("python", {endpoint_script, "lookup"}, el.text)
      return pandoc.RawBlock("html", converted_code)
  end
end

function Pandoc(doc)

  -- Don't do anything if we don't have to
  if missingMarimoCell then
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

  -- Flush the endpoint such that dupe cells are not registered
  pandoc.pipe("python", {endpoint_script, "flush"}, "")
  return doc
end
