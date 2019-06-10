define([
    'underscore',
    'jquery',
    'arches',
    'knockout',
    'models/graph',
    'viewmodels/card',
    'viewmodels/tile',
    // 'viewmodels/card-component',
    'viewmodels/provisional-tile',
    'viewmodels/alert'
], function(_, $, arches, ko, GraphModel, CardViewModel, TileViewModel, ProvisionalTileViewModel, AlertViewModel) {
    function viewModel(params) {
        var self = this;
        var url = arches.urls.api_card + (ko.unwrap(params.resourceid) || ko.unwrap(params.graphid));

        this.card = ko.observable();
        this.tile = ko.observable();
        this.tileArr = ko.observableArray();
        this.loading = params.loading || ko.observable(false);
        this.alert = params.alert || ko.observable(null);
        this.resourceId = params.resourceid;
        this.complete = params.complete || ko.observable();

        this.remove = function(tile) {
            // self.tileArr(tile);
            var tilesIdx = self.card().tiles().indexOf(tile);
            var arrIdx = self.tileArr.indexOf(tile);
            // console.log(self.card().tiles());
            self.card().tiles().splice(tilesIdx, 1);
            self.tileArr.splice(arrIdx, 1);
            console.log("removed");
            console.log(self.card().tiles());
        };

        this.edit = function(tile) {
            //
        }
        // this.agencyName = ko.computed({});

        this.loading(true);

        $.getJSON(url, function(data) {
            var handlers = {
                'after-update': [],
                'tile-reset': []
            };
            var displayname = ko.observable(data.displayname);
            var createLookup = function(list, idKey) {
                return _.reduce(list, function(lookup, item) {
                    lookup[item[idKey]] = item;
                    return lookup;
                }, {});
            };
            var flattenTree = function(parents, flatList) {
                _.each(ko.unwrap(parents), function(parent) {
                    flatList.push(parent);
                    var childrenKey = parent.tiles ? 'tiles' : 'cards';
                    flattenTree(
                        ko.unwrap(parent[childrenKey]),
                        flatList
                    );
                });
                return flatList;
            };

            self.reviewer = data.userisreviewer;
            self.provisionalTileViewModel = new ProvisionalTileViewModel({
                tile: self.tile,
                reviewer: data.userisreviewer
            });

            var graphModel = new GraphModel({
                data: {
                    nodes: data.nodes,
                    nodegroups: data.nodegroups,
                    edges: []
                },
                datatypes: data.datatypes
            });

            var topCards = _.filter(data.cards, function(card) {
                var nodegroup = _.find(data.nodegroups, function(group) {
                    return group.nodegroupid === card.nodegroup_id;
                });
                return !nodegroup || !nodegroup.parentnodegroup_id;
            }).map(function(card) {
                params.nodegroupid = params.nodegroupid || card.nodegroup_id;
                return new CardViewModel({
                    card: card,
                    graphModel: graphModel,
                    tile: null,
                    resourceId: self.resourceId,
                    displayname: displayname,
                    handlers: handlers,
                    cards: data.cards,
                    tiles: data.tiles,
                    provisionalTileViewModel: self.provisionalTileViewModel,
                    cardwidgets: data.cardwidgets,
                    userisreviewer: data.userisreviewer,
                    loading: self.loading
                });
            });

            topCards.forEach(function(topCard) {
                topCard.topCards = topCards;
            });

            self.widgetLookup = createLookup(
                data.widgets,
                'widgetid'
            );
            self.cardComponentLookup = createLookup(
                data['card_components'],
                'componentid'
            );
            self.nodeLookup = createLookup(
                graphModel.get('nodes')(),
                'nodeid'
            );
            self.on = function(eventName, handler) {
                if (handlers[eventName]) {
                    handlers[eventName].push(handler);
                }
            };

            flattenTree(topCards, []).forEach(function(item) {
                if (item.constructor.name === 'CardViewModel' && item.nodegroupid === ko.unwrap(params.nodegroupid)) {
                    if (ko.unwrap(params.parenttileid) && item.parent && ko.unwrap(params.parenttileid) !== item.parent.tileid) {
                        return;
                    }
                    self.card(item);
                    if (ko.unwrap(params.tileid)) {
                        ko.unwrap(item.tiles).forEach(function(tile) {
                            if (tile.tileid === ko.unwrap(params.tileid)) {
                                self.tile(tile);
                            }
                        });
                    } else {
                        self.tile(item.getNewTile());
                    }
                }
            });
            self.loading(false);
            self.complete(!!ko.unwrap(params.tileid));
        });

        this.tileArr = ko.observableArray();

        self.saveTile = function(tile, callback) {
            // self.tile() is the TileViewModel
            // self.card().tile() is not a thing

            self.loading(true);
            console.log("here's self.tile");
            console.log(self.tile());
            console.log("and self.card()");
            console.log(self.card());

            // self.tileArr = self.card().tiles.subscribe(function(list){
            //     return (list);
            // });

            tile.save(function(response) { //onFail, onSuccess
                self.loading(false);
                self.alert(
                    new AlertViewModel(
                        'ep-alert-red',
                        response.responseJSON.message[0],
                        response.responseJSON.message[1],
                        null,
                        function(){ return; }
                    )
                );
            }, function(tile) { //onSuccess

                console.log(params);
                console.log(tile);

                var newTile = new TileViewModel({
                    tile: tile,
                    card: self.card,
                    graphModel: params.graphModel,
                    resourceId: params.resourceId,
                    displayname: params.displayname,
                    handlers: params.handlers,
                    userisreviewer: params.userisreviewer,
                    cards: self.tile.cards,
                    tiles: [],
                    provisionalTileViewModel: params.provisionalTileViewModel,
                    selection: ko.observable(false),
                    scrollTo: ko.observable(),
                    loading: ko.observable(),
                    filter: ko.observable(),
                    cardwidgets: params.cardwidgets,
                });

                self.tileArr.push(newTile);
    
                // console.log("newTile");
                // console.log(newTile);
                
                // self.tileArr.push
                console.log(self.card().tiles());
   
                params.resourceid(tile.resourceinstance_id);
                params.tileid(tile.tileid);
                self.resourceId(tile.resourceinstance_id);
                self.complete(true);
                if (typeof callback === 'function') {
                    callback.apply(null, arguments);
                }
                self.tile(self.card().getNewTile()); //this appears to be working
                // console.log(self.card().isChildSelected());
   
                self.loading(false);
            });
        };
    }
    ko.components.register('add-ref-number-step', {
        viewModel: viewModel,
        template: {
            require: 'text!templates/views/components/workflows/add-ref-number-step.htm'
        }
    });
    return viewModel;
});
