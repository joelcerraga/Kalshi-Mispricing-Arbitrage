import unittest, numpy as np
from decimal import Decimal as D
from kalshi_engine.microstructure import Book, FeePolicy, levels, execution_fee, sweep
from kalshi_engine.arbitrage import partition_audit,temperature_payoff_states,coherence,basket,statewise_portfolio,expected_edge
from kalshi_engine.probability import normalise,calibrate,scores,fit_temperature,paired_block_interval

def book(bid='.40',ask='.45',depth='100'):
    return Book.from_payload({'yes_dollars':[[bid,depth]],'no_dollars':[[str(D(1)-D(ask)),depth]]})
def markets():
    base={'market_type':'binary','notional_value_dollars':'1','event_ticker':'E','rules_secondary':''}
    return [base|{'ticker':'L','strike_type':'less','cap_strike':60},base|{'ticker':'B','strike_type':'between','floor_strike':60,'cap_strike':61},base|{'ticker':'H','strike_type':'greater','floor_strike':61}]

class EngineTests(unittest.TestCase):
    def test_complement_ask(self):self.assertEqual(book().asks('yes')[0][0],D('.45'))
    def test_bids_sorted(self):self.assertEqual(levels([['.2','5'],['.7','2']])[0][0],D('.7'))
    def test_duplicates_aggregate(self):self.assertEqual(levels([['.2','5'],['.2','2']]),[(D('.2'),D(7))])
    def test_fractional_depth(self):self.assertEqual(levels([['.4321','2.57']])[0],(D('.4321'),D('2.57')))
    def test_invalid_numbers(self):
        for p,q in [('NaN','1'),('1.1','1'),('.3','-1')]:
            with self.assertRaises(ValueError):levels([[p,q]])
    def test_empty_not_zero_price(self):self.assertFalse(Book.from_payload({}).metrics()['two_sided'])
    def test_crossed_rejected(self):self.assertEqual(basket([book('.6','.5'),book()], 'yes',1,partition_verified=True)['status'],'blocked_crossed_book')
    def test_imbalance(self):self.assertEqual(book().metrics()['imbalance'],0)
    def test_depth_sweep(self):
        b=Book.from_payload({'yes_dollars':[['.3','100']],'no_dollars':[['.6','2'],['.5','8']]})
        r=sweep(b,'yes',5);self.assertAlmostEqual(r['purchase_cost'],2.3);self.assertEqual(r['levels'],2)
    def test_insufficient_no_partial_success(self):self.assertFalse(sweep(book(depth='1.5'),'yes',2)['fillable'])
    def test_quantity_positive(self):
        with self.assertRaises(ValueError):sweep(book(),'yes',0)
    def test_invalid_side(self):
        with self.assertRaises(ValueError):book().asks('wrong')
    def test_fee_half_price(self):self.assertEqual(execution_fee([('.5','100')]),D('1.75'))
    def test_direct_precision(self):self.assertEqual(execution_fee([('.5','1')]),D('.0175'))
    def test_cent_precision(self):self.assertEqual(execution_fee([('.5','1')],FeePolicy(balance_precision=D('.01'))),D('.02'))
    def test_rounding_accumulator(self):
        fee=execution_fee([('.5','1')]*100,FeePolicy(balance_precision=D('.01')))
        self.assertEqual(fee,D('1.75'))
    def test_zero_fees(self):self.assertEqual(execution_fee([('.5','1')],FeePolicy(multiplier=D('0'))),D('0'))
    def test_unknown_fee_fail_closed(self):
        with self.assertRaises(ValueError):FeePolicy.from_series({'fee_type':'new_type','fee_multiplier':1})
    def test_fee_multiplier(self):self.assertEqual(execution_fee([('.5','100')],FeePolicy(multiplier=D('2'))),D('3.50'))
    def test_partition(self):self.assertTrue(partition_audit(markets())['valid'])
    def test_full_precision_gap_state(self):
        m=markets();m[1]['cap_strike']=61;m[2]['floor_strike']=62
        a=temperature_payoff_states(m);self.assertTrue(np.any(a.sum(axis=1)==0))
    def test_actual_temperature_partition_gap(self):
        base={'market_type':'binary','notional_value_dollars':'1','event_ticker':'E'}
        m=[base|{'ticker':'L','strike_type':'less','cap_strike':60},base|{'ticker':'B','strike_type':'between','floor_strike':60,'cap_strike':61},base|{'ticker':'C','strike_type':'between','floor_strike':62,'cap_strike':63},base|{'ticker':'H','strike_type':'greater','floor_strike':63}]
        self.assertTrue(partition_audit(m)['valid']);self.assertFalse(partition_audit(m)['full_precision_exhaustive'])
    def test_gap(self):
        m=markets();m[1]['floor_strike']=61;self.assertFalse(partition_audit(m)['valid'])
    def test_overlap(self):
        m=markets();m[1]['floor_strike']=59;self.assertFalse(partition_audit(m)['valid'])
    def test_wrong_event(self):
        m=markets();m[0]['event_ticker']='F';self.assertFalse(partition_audit(m)['valid'])
    def test_non_exhaustive(self):self.assertFalse(partition_audit(markets()[1:])['valid'])
    def test_scalar_warning(self):
        m=markets();m[0]['rules_secondary']='last fair price';self.assertTrue(partition_audit(m)['exceptional_fair_value'])
    def test_midpoint_gap_not_arb(self):self.assertTrue(coherence([.2,.2,.2],[.4,.4,.4])['feasible'])
    def test_true_basket(self):self.assertTrue(basket([book('.29','.30')]*3,'yes',1,partition_verified=True)['strict_eligible'])
    def test_fee_erased_gap(self):self.assertLess(basket([book('.32','.33')]*3,'yes',1,partition_verified=True)['net_payoff'],0)
    def test_skew_blocks(self):self.assertFalse(basket([book('.29','.30')]*3,'yes',1,partition_verified=True,observation_span=3)['strict_eligible'])
    def test_exception_blocks(self):self.assertFalse(basket([book('.29','.30')]*3,'yes',1,partition_verified=True,exceptional=True)['strict_eligible'])
    def test_unverified_blocks(self):self.assertEqual(basket([book()]*3,'yes',1)['status'],'blocked_unverified_partition')
    def test_no_basket_payout(self):self.assertEqual(basket([book('.7','.71')]*3,'no',2,partition_verified=True)['ordinary_payout'],4)
    def test_lp_known_solution(self):
        r=statewise_portfolio(np.eye(3),[.3]*3,[10]*3,100);self.assertAlmostEqual(r['worst_profit'],1,places=7)
    def test_lp_no_opportunity(self):self.assertAlmostEqual(statewise_portfolio(np.eye(3),[.4]*3,[10]*3)['worst_profit'],0)
    def test_lp_missing_state(self):
        A=np.vstack([np.eye(3),np.zeros(3)]);self.assertAlmostEqual(statewise_portfolio(A,[.3]*3,[10]*3)['worst_profit'],0)
    def test_expected_edge_not_guarantee(self):self.assertAlmostEqual(expected_edge(.7,.65),.05)
    def test_normalise(self):self.assertAlmostEqual(sum(normalise([.3,.3,.3])),1)
    def test_temperature_identity(self):np.testing.assert_allclose(calibrate([.2,.3,.5],1),[.2,.3,.5])
    def test_temperature_order(self):self.assertGreater(calibrate([.2,.8],.5)[1],.8)
    def test_scores_perfect(self):self.assertAlmostEqual(scores([0,1],1)['brier'],0)
    def test_calibration_recovery(self):
        es=[{'p':[.1,.9],'winner':i%2} for i in range(100)]
        self.assertGreater(fit_temperature(es)['temperature'],3.9)
    def test_block_constant(self):
        r=paired_block_interval([.2]*18);self.assertAlmostEqual(r['lower'],.2);self.assertAlmostEqual(r['upper'],.2)
    def test_random_coherent_false_positives(self):
        rng=np.random.default_rng(20)
        for _ in range(200):
            p=rng.dirichlet(np.ones(6)*5);b=np.maximum(0,p-.01);a=np.minimum(1,p+.01)
            self.assertTrue(coherence(b,a)['feasible'])

if __name__=='__main__':unittest.main()
