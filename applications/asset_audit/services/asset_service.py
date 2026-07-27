from ..models import Asset


class AssetService:
    def __init__(self):
        self._items = {}

    def list_assets(self):
        return tuple(self._items.values())

    def get_asset(self, asset_id):
        try:
            return self._items[asset_id]
        except KeyError as exc:
            raise KeyError(f"Asset não encontrado: {asset_id}.") from exc

    def add_asset(self, asset):
        if not isinstance(asset, Asset):
            raise TypeError("asset deve ser um Asset.")
        if asset.id in self._items:
            raise ValueError(f"Asset já cadastrado: {asset.id}.")
        self._items[asset.id] = asset
        return asset

    def count_assets(self):
        return len(self._items)
