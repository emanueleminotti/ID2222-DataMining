package se.kth.jabeja;

import java.util.HashMap;
import se.kth.jabeja.config.Config;
import se.kth.jabeja.rand.RandNoGenerator;

public class SA_Jabeja extends Jabeja {

    private float T;

    public SA_Jabeja(HashMap<Integer, Node> graph, Config config) {
        super(graph, config);
        this.T = config.getTemperature();
    }

    @Override
    protected void endOfRound() {
        // Geometric cooling
        T = T * (1 - config.getDelta());

        // Restart mechanism
        if (T < 0.01) {
            T = config.getTemperature();
        }
    }

    @Override
    protected boolean acceptMove(double newUtility, double oldUtility) {
        double diff = newUtility - oldUtility;
        double acceptanceProbability = Math.exp(diff / T);
        return acceptanceProbability > Math.random();
    }

    // @Override
    // protected boolean acceptMove(double newUtility, double oldUtility) {
    //     double acceptanceFactor = 1.0 / T;
    //     return (newUtility / Math.pow(oldUtility, acceptanceFactor)) > 1.0;
    // }
}