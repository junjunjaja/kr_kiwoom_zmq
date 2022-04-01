from collections import defaultdict

class ind_stock(object):
    def __init__(self, price_d1, stock_num):
        self.__price_d1 = price_d1
        self.__stock_num = stock_num
        self.bid_price = 0
        self.ask_price = 0
        self.v_bid_price =0
        self.v_ask_price = 0
        self.bid_traded_volume = 0
        self.ask_traded_volume = 0
        self.ask_total_remain = 0
        self.bid_total_remain = 0
        self.bid_cancel_total =0
        self.ask_cancel_total = 0
        self.__cancel_adj_ratio = 1/5


    @property
    def total_a(self):
        return self.__price_d1 * self.__stock_num
    @property
    def bid_trade_p(self):
        return (self.bid_traded_volume*self.v_bid_price)/(self.total_a)
    @property
    def ask_trade_p(self):
        return (self.ask_traded_volume*self.v_ask_price) / (self.total_a)
    @property
    def trade_p(self):
        return (self.ask_traded_volume*self.v_ask_price+self.bid_traded_volume*self.v_bid_price) / (self.total_a)
    @property
    def vwap(self):
        return (self.ask_traded_volume*self.v_ask_price+self.bid_traded_volume*self.v_bid_price)/(self.ask_traded_volume + self.bid_traded_volume)
    @property
    def v_ratio(self):
        return (self.ask_traded_volume*self.v_ask_price-self.bid_traded_volume*self.v_bid_price)/(self.ask_traded_volume*self.v_ask_price+self.bid_traded_volume*self.v_bid_price)

    @property
    def balance_bid_impact(self):
        p1 = self.v_bid_price if abs(self.v_bid_price) > 1e-4 else self.__price_d1
        return (self.bid_total_remain*p1) / (self.total_a)
    @property
    def balance_ask_impact(self):
        p1 = self.v_ask_price if abs(self.v_ask_price) > 1e-4 else self.__price_d1
        return (p1*self.ask_total_remain) / (self.total_a)
    @property
    def balance_impact(self):
        p1 = self.v_ask_price if abs(self.v_ask_price) > 1e-4 else self.__price_d1
        p2 = self.v_bid_price if abs(self.v_bid_price) > 1e-4 else self.__price_d1
        return (self.ask_total_remain*p1+self.bid_total_remain*p2) / (self.total_a)
    @property
    def balance_bid_impact_adj(self):
        p1 = self.bid_price if abs(self.bid_price) > 1e-4 else self.__price_d1
        p2 = self.v_bid_price if abs(self.v_bid_price) > 1e-4 else p1
        return (self.bid_total_remain*p1-self.bid_cancel_total*p1*self.__cancel_adj_ratio + self.bid_traded_volume*p2) / (self.total_a)

    @property
    def balance_ask_impact_adj(self):
        p1 = self.ask_price if abs(self.ask_price) > 1e-4 else self.__price_d1
        p2 = self.v_ask_price if abs(self.v_ask_price) > 1e-4 else p1
        return (self.ask_total_remain*p1-self.ask_cancel_total*p1*self.__cancel_adj_ratio + self.ask_traded_volume*p2) / (self.total_a)
    @property
    def balance_impact_adj(self):
        p1 = self.bid_price if abs(self.bid_price) > 1e-4 else self.__price_d1
        p2 = self.v_bid_price if abs(self.v_bid_price) > 1e-4 else p1
        p3 = self.ask_price if abs(self.ask_price) > 1e-4 else self.__price_d1
        p4 = self.v_ask_price if abs(self.v_ask_price) > 1e-4 else p1
        return ((self.ask_total_remain*p3-self.ask_cancel_total*p3*self.__cancel_adj_ratio + self.ask_traded_volume*p4)+(self.bid_total_remain*p1-self.bid_cancel_total*p1*self.__cancel_adj_ratio + self.bid_traded_volume*p2)) / (self.total_a)




class Base_AM(object):
    def __init__(self,stock_item):
        self.Univ = stock_item.keys()
        self.Sig_Target = defaultdict(ind_stock)

